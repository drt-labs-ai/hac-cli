"""HAC HTTP client — Spring Security form login, CSRF token management, Groovy execution.

Auth flow per request:
  1. GET  /login                          → parse CSRF token for login form
  2. POST /j_spring_security_check        → follow_redirects=False; inspect redirect location
  3. GET  /console/scripting/api/         → parse CSRF token for execute calls
  4. POST /console/scripting/api/execute  → X-CSRF-TOKEN header; parse JSON response

Sessions (cookie jars) are cached in memory with a 30-minute TTL. On expiry or a
401/403 response, the client re-authenticates once before raising.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
from bs4 import BeautifulSoup, Tag

from hac_cli.domain.exceptions import (
    HacAuthenticationError,
    HacConnectionError,
    MissingCredentialsError,
    ScriptExecutionError,
)
from hac_cli.domain.models import Environment, ExecutionContext, ExecutionResult, ExecutionStatus
from hac_cli.domain.ports import IHacClient, ISecretStore
from hac_cli.utils.logging import get_logger

_LOG = get_logger(__name__)
_SESSION_TTL: float = 1800.0  # 30 minutes
_USER_AGENT = "hac-cli/0.1.0"


@dataclass
class _CachedSession:
    cookies: dict[str, str]
    created_at: float = field(default_factory=time.monotonic)

    def is_expired(self, ttl: float = _SESSION_TTL) -> bool:
        return time.monotonic() - self.created_at > ttl


class HacHttpClient(IHacClient):
    def __init__(self, secret_store: ISecretStore) -> None:
        self._secrets = secret_store
        self._sessions: dict[str, _CachedSession] = {}

    async def execute(self, ctx: ExecutionContext) -> ExecutionResult:
        start = time.monotonic()
        env = ctx.environment

        async with self._make_client(env) as client:
            if not self._has_valid_session(env.name):
                await self._authenticate(client, env)

            try:
                csrf = await self._fetch_csrf_token(client, env)
            except HacAuthenticationError:
                # Server-side session expired — re-authenticate once
                self._invalidate_session(env.name)
                await self._authenticate(client, env)
                csrf = await self._fetch_csrf_token(client, env)

            try:
                result = await self._post_script(client, ctx, csrf)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (401, 403):
                    self._invalidate_session(env.name)
                    await self._authenticate(client, env)
                    csrf = await self._fetch_csrf_token(client, env)
                    result = await self._post_script(client, ctx, csrf)
                else:
                    raise HacConnectionError(
                        env.hac_base_url, f"HTTP {exc.response.status_code}"
                    ) from exc

        result.execution_time_ms = int((time.monotonic() - start) * 1000)
        result.environment_name = env.name
        return result

    async def test_connection(self, env: Environment) -> bool:
        try:
            async with self._make_client(env) as client:
                await self._authenticate(client, env)
                await self._fetch_csrf_token(client, env)
            return True
        except (HacAuthenticationError, HacConnectionError, MissingCredentialsError):
            return False
        except Exception as exc:
            _LOG.debug("Unexpected error testing %s: %s", env.name, exc)
            return False

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _make_client(self, env: Environment) -> httpx.AsyncClient:
        session = self._sessions.get(env.name)
        cookies: dict[str, str] = (
            session.cookies if session and not session.is_expired() else {}
        )
        return httpx.AsyncClient(
            verify=env.verify_ssl,
            timeout=float(env.timeout),
            follow_redirects=True,
            cookies=cookies,
            headers={"User-Agent": _USER_AGENT},
        )

    def _has_valid_session(self, env_name: str) -> bool:
        session = self._sessions.get(env_name)
        return session is not None and not session.is_expired()

    def _invalidate_session(self, env_name: str) -> None:
        self._sessions.pop(env_name, None)

    async def _authenticate(self, client: httpx.AsyncClient, env: Environment) -> None:
        password = self._secrets.get_password(env.name)
        if not password:
            raise MissingCredentialsError(env.name)

        _LOG.debug("Authenticating to %s as %s", env.name, env.username)

        try:
            login_page = await client.get(env.login_page_url)
            csrf_for_login = self._extract_csrf_from_html(login_page.text)

            login_data: dict[str, str] = {
                "j_username": env.username,
                "j_password": password,
            }
            if csrf_for_login:
                login_data["_csrf"] = csrf_for_login

            resp = await client.post(
                env.login_url,
                data=login_data,
                follow_redirects=False,
            )
        except httpx.ConnectError as exc:
            raise HacConnectionError(env.hac_base_url, str(exc)) from exc
        except httpx.TimeoutException:
            raise HacConnectionError(env.hac_base_url, "Connection timed out")

        if self._is_login_failure(resp):
            raise HacAuthenticationError(env.name)

        self._sessions[env.name] = _CachedSession(cookies=dict(client.cookies))
        _LOG.debug("Authentication successful for %s", env.name)

    async def _fetch_csrf_token(self, client: httpx.AsyncClient, env: Environment) -> str:
        try:
            resp = await client.get(env.scripting_url)
        except httpx.ConnectError as exc:
            raise HacConnectionError(env.hac_base_url, str(exc)) from exc
        except httpx.TimeoutException:
            raise HacConnectionError(env.hac_base_url, "Timed out fetching scripting page")

        # When the session is invalid, HAC redirects to the login page
        if "login" in str(resp.url).lower():
            raise HacAuthenticationError(env.name)

        resp.raise_for_status()

        csrf = self._extract_csrf_from_html(resp.text)
        if not csrf:
            raise ScriptExecutionError(
                env.name,
                "Could not extract CSRF token from HAC scripting page. "
                "Verify the URL points to a valid SAP Commerce HAC instance.",
            )
        return csrf

    async def _post_script(
        self,
        client: httpx.AsyncClient,
        ctx: ExecutionContext,
        csrf_token: str,
    ) -> ExecutionResult:
        try:
            resp = await client.post(
                ctx.environment.execute_url,
                data={
                    "script": ctx.script_content,
                    "commit": str(ctx.commit).lower(),
                },
                headers={
                    "X-CSRF-TOKEN": csrf_token,
                    "Accept": "application/json",
                },
            )
            resp.raise_for_status()
        except httpx.TimeoutException:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                output="",
                execution_time_ms=0,
                stack_trace=f"Script execution timed out after {ctx.effective_timeout}s",
            )

        try:
            payload: dict = resp.json()
        except Exception as exc:
            raise ScriptExecutionError(
                ctx.environment.name,
                f"Unexpected HAC response (not JSON): {resp.text[:300]}",
            ) from exc

        return self._parse_execution_response(payload)

    @staticmethod
    def _parse_execution_response(payload: dict) -> ExecutionResult:
        stacktrace_occurred: bool = payload.get("stacktraceOccurred", False)

        if stacktrace_occurred:
            # outputText = stdout captured before the error
            # executionResult = the stacktrace itself
            output = (payload.get("outputText") or "").strip()
            stack_trace: Optional[str] = (payload.get("executionResult") or "").strip() or None
        else:
            output = (
                payload.get("outputText") or payload.get("executionResult") or ""
            ).strip()
            stack_trace = None

        return ExecutionResult(
            status=ExecutionStatus.ERROR if stacktrace_occurred else ExecutionStatus.SUCCESS,
            output=output,
            execution_time_ms=0,
            stack_trace=stack_trace,
        )

    @staticmethod
    def _extract_csrf_from_html(html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "lxml")

        # Standard Spring Security CSRF meta tag
        meta = soup.find("meta", attrs={"name": "_csrf"})
        if isinstance(meta, Tag):
            content = meta.get("content")
            if content:
                return str(content)

        # Hidden input field (login form pages)
        hidden = soup.find("input", attrs={"name": "_csrf"})
        if isinstance(hidden, Tag):
            value = hidden.get("value")
            if value:
                return str(value)

        return None

    @staticmethod
    def _is_login_failure(resp: httpx.Response) -> bool:
        if resp.status_code >= 400:
            return True
        if resp.is_redirect:
            location = resp.headers.get("location", "").lower()
            return "error" in location
        return False
