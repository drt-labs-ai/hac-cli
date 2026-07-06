"""Unit tests for HacHttpClient."""

from __future__ import annotations

from typing import Optional

import httpx
import pytest
from pytest_httpx import HTTPXMock

from hac_cli.domain.exceptions import (
    HacAuthenticationError,
    HacConnectionError,
    MissingCredentialsError,
    ScriptExecutionError,
)
from hac_cli.domain.models import Environment, ExecutionContext, ExecutionResult, ExecutionStatus
from hac_cli.domain.ports import ISecretStore
from hac_cli.infrastructure.hac_client import HacHttpClient, _CachedSession

# ---------------------------------------------------------------------------
# Shared HTML fixtures
# ---------------------------------------------------------------------------

_LOGIN_PAGE_WITH_CSRF = """
<html><body>
<form action="/j_spring_security_check">
  <input type="hidden" name="_csrf" value="csrf-login-token-123"/>
</form>
</body></html>
"""

_LOGIN_PAGE_NO_CSRF = """
<html><body>
<form action="/j_spring_security_check"></form>
</body></html>
"""

_SCRIPTING_PAGE = """
<html><head>
<meta name="_csrf" content="csrf-execute-token-456"/>
<meta name="_csrf_header" content="X-CSRF-TOKEN"/>
</head><body>Scripting Console</body></html>
"""

_SCRIPTING_PAGE_NO_CSRF = """
<html><body>Scripting Console — missing CSRF token</body></html>
"""

_SUCCESS_PAYLOAD = {"executionResult": "hello world", "stacktraceOccurred": False}
_ERROR_PAYLOAD = {
    "executionResult": "groovy.lang.MissingMethodException: No signature of method...",
    "stacktraceOccurred": True,
    "outputText": "output before error",
}
_ERROR_PAYLOAD_NO_OUTPUTTEXT = {
    "executionResult": "groovy.lang.MissingMethodException: ...",
    "stacktraceOccurred": True,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _MockSecretStore(ISecretStore):
    def __init__(self, password: Optional[str] = "test_password") -> None:
        self._password = password

    def get_password(self, env_name: str) -> Optional[str]:
        return self._password

    def set_password(self, env_name: str, password: str) -> None:
        pass

    def delete_password(self, env_name: str) -> None:
        pass


def _mock_full_auth_flow(
    httpx_mock: HTTPXMock,
    env: Environment,
    execute_payload: dict,
) -> None:
    """Register the four HTTP calls that a fresh (unauthenticated) execute needs."""
    httpx_mock.add_response(method="GET", url=env.login_page_url, text=_LOGIN_PAGE_WITH_CSRF)
    httpx_mock.add_response(
        method="POST",
        url=env.login_url,
        status_code=302,
        headers={"location": f"{env.hac_base_url}/"},
    )
    httpx_mock.add_response(method="GET", url=env.scripting_url, text=_SCRIPTING_PAGE)
    httpx_mock.add_response(method="POST", url=env.execute_url, json=execute_payload)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def env() -> Environment:
    return Environment(
        name="dev",
        url="https://dev-hac.example.com",
        username="admin",
        timeout=5,
        verify_ssl=False,
    )


@pytest.fixture
def client() -> HacHttpClient:
    return HacHttpClient(secret_store=_MockSecretStore())


@pytest.fixture
def ctx(env: Environment) -> ExecutionContext:
    return ExecutionContext(
        environment=env,
        script_content='println "hello"',
        commit=False,
    )


# ---------------------------------------------------------------------------
# Static helper tests — no HTTP
# ---------------------------------------------------------------------------


class TestExtractCsrfFromHtml:
    def test_meta_tag(self):
        html = '<html><head><meta name="_csrf" content="token-abc"/></head></html>'
        assert HacHttpClient._extract_csrf_from_html(html) == "token-abc"

    def test_hidden_input(self):
        html = '<html><body><input type="hidden" name="_csrf" value="token-xyz"/></body></html>'
        assert HacHttpClient._extract_csrf_from_html(html) == "token-xyz"

    def test_meta_takes_priority_over_input(self):
        html = """
        <html>
          <head><meta name="_csrf" content="meta-token"/></head>
          <body><input name="_csrf" value="input-token"/></body>
        </html>
        """
        assert HacHttpClient._extract_csrf_from_html(html) == "meta-token"

    def test_returns_none_when_missing(self):
        assert HacHttpClient._extract_csrf_from_html("<html><body>nothing</body></html>") is None

    def test_returns_none_for_empty_html(self):
        assert HacHttpClient._extract_csrf_from_html("") is None

    def test_meta_with_empty_content_is_ignored(self):
        html = '<html><head><meta name="_csrf" content=""/></head></html>'
        assert HacHttpClient._extract_csrf_from_html(html) is None


class TestIsLoginFailure:
    def test_4xx_is_failure(self):
        assert HacHttpClient._is_login_failure(httpx.Response(403)) is True

    def test_5xx_is_failure(self):
        assert HacHttpClient._is_login_failure(httpx.Response(503)) is True

    def test_redirect_with_error_is_failure(self):
        resp = httpx.Response(302, headers={"location": "/login?error=true"})
        assert HacHttpClient._is_login_failure(resp) is True

    def test_redirect_with_error_case_insensitive(self):
        resp = httpx.Response(302, headers={"location": "/Login?ERROR=true"})
        assert HacHttpClient._is_login_failure(resp) is True

    def test_redirect_to_app_is_success(self):
        resp = httpx.Response(302, headers={"location": "/hac/"})
        assert HacHttpClient._is_login_failure(resp) is False

    def test_200_is_success(self):
        assert HacHttpClient._is_login_failure(httpx.Response(200)) is False


class TestParseExecutionResponse:
    def test_success_response(self):
        result = HacHttpClient._parse_execution_response(
            {"executionResult": "hello", "stacktraceOccurred": False}
        )
        assert result.succeeded
        assert result.output == "hello"
        assert result.stack_trace is None

    def test_error_response_separates_output_and_stacktrace(self):
        result = HacHttpClient._parse_execution_response(
            {
                "executionResult": "groovy.lang.MissingMethodException: ...",
                "outputText": "printed before error",
                "stacktraceOccurred": True,
            }
        )
        assert not result.succeeded
        assert result.output == "printed before error"
        assert result.stack_trace == "groovy.lang.MissingMethodException: ..."

    def test_error_response_without_outputtext(self):
        result = HacHttpClient._parse_execution_response(
            {"executionResult": "stacktrace here", "stacktraceOccurred": True}
        )
        assert not result.succeeded
        assert result.output == ""
        assert result.stack_trace == "stacktrace here"

    def test_success_prefers_outputtext_over_executionresult(self):
        result = HacHttpClient._parse_execution_response(
            {
                "outputText": "from outputText",
                "executionResult": "from executionResult",
                "stacktraceOccurred": False,
            }
        )
        assert result.output == "from outputText"

    def test_output_is_stripped(self):
        result = HacHttpClient._parse_execution_response(
            {"executionResult": "  whitespace  \n", "stacktraceOccurred": False}
        )
        assert result.output == "whitespace"

    def test_missing_stacktrace_flag_defaults_to_success(self):
        result = HacHttpClient._parse_execution_response({"executionResult": "ok"})
        assert result.succeeded


# ---------------------------------------------------------------------------
# execute() — full HTTP flow tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_success_full_flow(
    httpx_mock: HTTPXMock, client: HacHttpClient, ctx: ExecutionContext
):
    _mock_full_auth_flow(httpx_mock, ctx.environment, _SUCCESS_PAYLOAD)

    result = await client.execute(ctx)

    assert result.succeeded
    assert result.output == "hello world"
    assert result.status == ExecutionStatus.SUCCESS
    assert result.environment_name == "dev"
    assert result.execution_time_ms >= 0


@pytest.mark.asyncio
async def test_execute_error_response(
    httpx_mock: HTTPXMock, client: HacHttpClient, ctx: ExecutionContext
):
    _mock_full_auth_flow(httpx_mock, ctx.environment, _ERROR_PAYLOAD)

    result = await client.execute(ctx)

    assert not result.succeeded
    assert result.status == ExecutionStatus.ERROR
    assert result.output == "output before error"
    assert result.stack_trace is not None
    assert "MissingMethodException" in result.stack_trace


@pytest.mark.asyncio
async def test_execute_sends_commit_true(
    httpx_mock: HTTPXMock, client: HacHttpClient, env: Environment
):
    commit_ctx = ExecutionContext(environment=env, script_content='println "x"', commit=True)
    _mock_full_auth_flow(httpx_mock, env, _SUCCESS_PAYLOAD)

    await client.execute(commit_ctx)

    execute_req = next(
        r for r in httpx_mock.get_requests() if "execute" in str(r.url)
    )
    assert b"commit=true" in execute_req.content


@pytest.mark.asyncio
async def test_execute_sends_commit_false_by_default(
    httpx_mock: HTTPXMock, client: HacHttpClient, ctx: ExecutionContext
):
    _mock_full_auth_flow(httpx_mock, ctx.environment, _SUCCESS_PAYLOAD)

    await client.execute(ctx)

    execute_req = next(
        r for r in httpx_mock.get_requests() if "execute" in str(r.url)
    )
    assert b"commit=false" in execute_req.content


@pytest.mark.asyncio
async def test_execute_sends_csrf_header(
    httpx_mock: HTTPXMock, client: HacHttpClient, ctx: ExecutionContext
):
    _mock_full_auth_flow(httpx_mock, ctx.environment, _SUCCESS_PAYLOAD)

    await client.execute(ctx)

    execute_req = next(
        r for r in httpx_mock.get_requests() if "execute" in str(r.url)
    )
    assert execute_req.headers["X-CSRF-TOKEN"] == "csrf-execute-token-456"


@pytest.mark.asyncio
async def test_execute_reuses_cached_session(
    httpx_mock: HTTPXMock, client: HacHttpClient, ctx: ExecutionContext
):
    """With a valid cached session, no login calls are made."""
    client._sessions["dev"] = _CachedSession(cookies={"JSESSIONID": "abc123"})

    httpx_mock.add_response(
        method="GET", url=ctx.environment.scripting_url, text=_SCRIPTING_PAGE
    )
    httpx_mock.add_response(
        method="POST", url=ctx.environment.execute_url, json=_SUCCESS_PAYLOAD
    )

    result = await client.execute(ctx)

    assert result.succeeded
    requests = httpx_mock.get_requests()
    assert not any("j_spring_security_check" in str(r.url) for r in requests)


@pytest.mark.asyncio
async def test_execute_reauths_when_scripting_page_redirects_to_login(
    httpx_mock: HTTPXMock, client: HacHttpClient, ctx: ExecutionContext
):
    """If the cached session is rejected by HAC, re-authenticate and retry."""
    client._sessions["dev"] = _CachedSession(cookies={"JSESSIONID": "stale"})
    env = ctx.environment

    # First CSRF fetch → redirect to login (session expired server-side)
    httpx_mock.add_response(
        method="GET",
        url=env.scripting_url,
        status_code=302,
        headers={"location": f"{env.hac_base_url}/login"},
    )
    httpx_mock.add_response(
        method="GET",
        url=env.login_page_url,
        text=_LOGIN_PAGE_HTML_AFTER_REDIRECT,
    )
    # Re-auth flow
    httpx_mock.add_response(method="GET", url=env.login_page_url, text=_LOGIN_PAGE_WITH_CSRF)
    httpx_mock.add_response(
        method="POST",
        url=env.login_url,
        status_code=302,
        headers={"location": f"{env.hac_base_url}/"},
    )
    # Second CSRF fetch succeeds
    httpx_mock.add_response(method="GET", url=env.scripting_url, text=_SCRIPTING_PAGE)
    httpx_mock.add_response(method="POST", url=env.execute_url, json=_SUCCESS_PAYLOAD)

    result = await client.execute(ctx)
    assert result.succeeded


_LOGIN_PAGE_HTML_AFTER_REDIRECT = _LOGIN_PAGE_WITH_CSRF


@pytest.mark.asyncio
async def test_execute_timeout_returns_timeout_status(
    httpx_mock: HTTPXMock, client: HacHttpClient, ctx: ExecutionContext
):
    client._sessions["dev"] = _CachedSession(cookies={"JSESSIONID": "abc123"})
    httpx_mock.add_response(method="GET", url=ctx.environment.scripting_url, text=_SCRIPTING_PAGE)
    httpx_mock.add_exception(
        exception=httpx.TimeoutException("timed out"),
        url=ctx.environment.execute_url,
    )

    result = await client.execute(ctx)

    assert result.status == ExecutionStatus.TIMEOUT
    assert result.stack_trace is not None
    assert "timed out" in result.stack_trace.lower()


@pytest.mark.asyncio
async def test_execute_raises_when_no_password(env: Environment):
    client_no_pass = HacHttpClient(secret_store=_MockSecretStore(password=None))
    ctx = ExecutionContext(environment=env, script_content='println "x"')

    with pytest.raises(MissingCredentialsError):
        await client_no_pass.execute(ctx)


@pytest.mark.asyncio
async def test_execute_raises_on_auth_failure(
    httpx_mock: HTTPXMock, client: HacHttpClient, ctx: ExecutionContext
):
    env = ctx.environment
    httpx_mock.add_response(method="GET", url=env.login_page_url, text=_LOGIN_PAGE_NO_CSRF)
    httpx_mock.add_response(
        method="POST",
        url=env.login_url,
        status_code=302,
        headers={"location": "/login?error=true"},
    )

    with pytest.raises(HacAuthenticationError):
        await client.execute(ctx)


@pytest.mark.asyncio
async def test_execute_raises_on_connect_error(
    httpx_mock: HTTPXMock, client: HacHttpClient, ctx: ExecutionContext
):
    httpx_mock.add_exception(
        exception=httpx.ConnectError("connection refused"),
        url=ctx.environment.login_page_url,
    )

    with pytest.raises(HacConnectionError):
        await client.execute(ctx)


@pytest.mark.asyncio
async def test_execute_raises_when_csrf_missing_from_scripting_page(
    httpx_mock: HTTPXMock, client: HacHttpClient, ctx: ExecutionContext
):
    httpx_mock.add_response(
        method="GET", url=ctx.environment.login_page_url, text=_LOGIN_PAGE_WITH_CSRF
    )
    httpx_mock.add_response(
        method="POST",
        url=ctx.environment.login_url,
        status_code=302,
        headers={"location": f"{ctx.environment.hac_base_url}/"},
    )
    httpx_mock.add_response(
        method="GET",
        url=ctx.environment.scripting_url,
        text=_SCRIPTING_PAGE_NO_CSRF,
    )

    with pytest.raises(ScriptExecutionError, match="CSRF token"):
        await client.execute(ctx)


# ---------------------------------------------------------------------------
# test_connection() tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_test_connection_returns_true_on_success(
    httpx_mock: HTTPXMock, client: HacHttpClient, env: Environment
):
    httpx_mock.add_response(method="GET", url=env.login_page_url, text=_LOGIN_PAGE_WITH_CSRF)
    httpx_mock.add_response(
        method="POST",
        url=env.login_url,
        status_code=302,
        headers={"location": f"{env.hac_base_url}/"},
    )
    httpx_mock.add_response(method="GET", url=env.scripting_url, text=_SCRIPTING_PAGE)

    assert await client.test_connection(env) is True


@pytest.mark.asyncio
async def test_test_connection_returns_false_on_bad_credentials(
    httpx_mock: HTTPXMock, client: HacHttpClient, env: Environment
):
    httpx_mock.add_response(method="GET", url=env.login_page_url, text=_LOGIN_PAGE_NO_CSRF)
    httpx_mock.add_response(
        method="POST",
        url=env.login_url,
        status_code=302,
        headers={"location": "/login?error=true"},
    )

    assert await client.test_connection(env) is False


@pytest.mark.asyncio
async def test_test_connection_returns_false_on_no_password(env: Environment):
    client_no_pass = HacHttpClient(secret_store=_MockSecretStore(password=None))
    assert await client_no_pass.test_connection(env) is False


@pytest.mark.asyncio
async def test_test_connection_returns_false_on_network_error(
    httpx_mock: HTTPXMock, client: HacHttpClient, env: Environment
):
    httpx_mock.add_exception(
        exception=httpx.ConnectError("no route"),
        url=env.login_page_url,
    )
    assert await client.test_connection(env) is False
