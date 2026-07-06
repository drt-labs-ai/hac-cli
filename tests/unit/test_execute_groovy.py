"""Unit tests for ExecuteGroovyService."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from hac_cli.application.execute_groovy import ExecuteGroovyService
from hac_cli.domain.exceptions import (
    CommitBlockedBySafeModeError,
    EnvironmentNotFoundError,
    MissingCredentialsError,
)
from hac_cli.domain.models import (
    Environment,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
    ScriptMeta,
)
from hac_cli.domain.ports import IConfigStore, IHacClient, IScriptRepository


# ---------------------------------------------------------------------------
# Minimal mock implementations
# ---------------------------------------------------------------------------


class _MockConfigStore(IConfigStore):
    def __init__(self, envs: dict[str, Environment] | None = None) -> None:
        self._envs = envs or {}

    def get_environment(self, name: str) -> Optional[Environment]:
        return self._envs.get(name)

    def list_environments(self) -> list[Environment]:
        return list(self._envs.values())

    def save_environment(self, env: Environment) -> None:
        self._envs[env.name] = env

    def delete_environment(self, name: str) -> None:
        self._envs.pop(name, None)


class _MockScriptRepo(IScriptRepository):
    def __init__(self, scripts: dict[str, str] | None = None) -> None:
        self._scripts = scripts or {"cache/clear_all": "println 'clearing'"}

    def list_scripts(self, category: Optional[str] = None) -> list[ScriptMeta]:
        return []

    def get_script_content(self, path: str) -> str:
        if path not in self._scripts:
            raise FileNotFoundError(path)
        return self._scripts[path]

    def search_scripts(self, query: str) -> list[ScriptMeta]:
        return []


def _make_success_result() -> ExecutionResult:
    return ExecutionResult(
        status=ExecutionStatus.SUCCESS,
        output="script output",
        execution_time_ms=42,
    )


def _make_service(
    env: Environment | None = None,
    hac_client: IHacClient | None = None,
    scripts: dict[str, str] | None = None,
) -> ExecuteGroovyService:
    envs = {env.name: env} if env else {}
    mock_client = hac_client or _make_mock_client()
    return ExecuteGroovyService(
        hac_client=mock_client,
        config_store=_MockConfigStore(envs),
        script_repo=_MockScriptRepo(scripts),
    )


def _make_mock_client(result: ExecutionResult | None = None) -> IHacClient:
    client = MagicMock(spec=IHacClient)
    client.execute = AsyncMock(return_value=result or _make_success_result())
    return client


@pytest.fixture
def dev_env() -> Environment:
    return Environment(
        name="dev", url="https://dev.example.com", username="admin", password="secret"
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExecuteGroovyService:
    @pytest.mark.asyncio
    async def test_execute_inline_code_success(self, dev_env: Environment):
        svc = _make_service(env=dev_env)

        result = await svc.execute(
            env_name="dev", inline_code='println "hello"'
        )

        assert result.succeeded

    @pytest.mark.asyncio
    async def test_execute_passes_inline_code_to_client(self, dev_env: Environment):
        mock_client = _make_mock_client()
        svc = _make_service(env=dev_env, hac_client=mock_client)

        await svc.execute(env_name="dev", inline_code='println "hi"')

        mock_client.execute.assert_awaited_once()
        ctx: ExecutionContext = mock_client.execute.call_args[0][0]
        assert ctx.script_content == 'println "hi"'
        assert ctx.commit is False

    @pytest.mark.asyncio
    async def test_execute_passes_commit_flag_when_safe_mode_disabled(self):
        env = Environment(
            name="dev", url="https://dev.example.com", username="admin",
            password="secret", safe_mode=False,
        )
        mock_client = _make_mock_client()
        svc = _make_service(env=env, hac_client=mock_client)

        await svc.execute(env_name="dev", inline_code='println "x"', commit=True)

        ctx: ExecutionContext = mock_client.execute.call_args[0][0]
        assert ctx.commit is True

    @pytest.mark.asyncio
    async def test_execute_raises_when_commit_on_safe_mode_env(self, dev_env: Environment):
        svc = _make_service(env=dev_env)

        with pytest.raises(CommitBlockedBySafeModeError) as exc_info:
            await svc.execute(env_name="dev", inline_code='println "x"', commit=True)

        assert "dev" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_allows_commit_false_on_safe_mode_env(self, dev_env: Environment):
        mock_client = _make_mock_client()
        svc = _make_service(env=dev_env, hac_client=mock_client)

        await svc.execute(env_name="dev", inline_code='println "x"', commit=False)

        ctx: ExecutionContext = mock_client.execute.call_args[0][0]
        assert ctx.commit is False

    @pytest.mark.asyncio
    async def test_execute_from_file_path(self, dev_env: Environment, tmp_path: Path):
        script_file = tmp_path / "test.groovy"
        script_file.write_text('println "from file"')
        mock_client = _make_mock_client()
        svc = _make_service(env=dev_env, hac_client=mock_client)

        await svc.execute(env_name="dev", file_path=script_file)

        ctx: ExecutionContext = mock_client.execute.call_args[0][0]
        assert ctx.script_content == 'println "from file"'

    @pytest.mark.asyncio
    async def test_execute_from_library_path(self, dev_env: Environment):
        mock_client = _make_mock_client()
        svc = _make_service(
            env=dev_env,
            hac_client=mock_client,
            scripts={"cache/clear_all": "println 'clearing'"},
        )

        await svc.execute(env_name="dev", script_library_path="cache/clear_all")

        ctx: ExecutionContext = mock_client.execute.call_args[0][0]
        assert ctx.script_content == "println 'clearing'"

    @pytest.mark.asyncio
    async def test_execute_raises_when_env_not_found(self):
        svc = _make_service()  # no environments registered

        with pytest.raises(EnvironmentNotFoundError) as exc_info:
            await svc.execute(env_name="nonexistent", inline_code='println "x"')

        assert "nonexistent" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_raises_when_no_password(self):
        env_no_pass = Environment(
            name="dev", url="https://dev.example.com", username="admin", password=None
        )
        svc = _make_service(env=env_no_pass)

        with pytest.raises(MissingCredentialsError) as exc_info:
            await svc.execute(env_name="dev", inline_code='println "x"')

        assert "dev" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_raises_when_no_source_given(self, dev_env: Environment):
        svc = _make_service(env=dev_env)

        with pytest.raises(ValueError, match="No script source"):
            await svc.execute(env_name="dev")

    @pytest.mark.asyncio
    async def test_execute_propagates_environment_to_client(self, dev_env: Environment):
        mock_client = _make_mock_client()
        svc = _make_service(env=dev_env, hac_client=mock_client)

        await svc.execute(env_name="dev", inline_code='println "x"')

        ctx: ExecutionContext = mock_client.execute.call_args[0][0]
        assert ctx.environment.name == "dev"
        assert ctx.environment.url == "https://dev.example.com"


class TestFindScriptsByNlp:
    def test_returns_matching_scripts(self, dev_env: Environment):
        repo = MagicMock(spec=IScriptRepository)
        expected = [
            ScriptMeta(name="Clear All Caches", description="", category="cache", path="cache/clear_all")
        ]
        repo.search_scripts.return_value = expected
        svc = ExecuteGroovyService(
            hac_client=MagicMock(),
            config_store=_MockConfigStore(),
            script_repo=repo,
        )

        results = svc.find_scripts_by_nlp("clear caches")

        repo.search_scripts.assert_called_once_with("clear caches")
        assert results == expected

    def test_returns_empty_when_no_match(self):
        repo = MagicMock(spec=IScriptRepository)
        repo.search_scripts.return_value = []
        svc = ExecuteGroovyService(
            hac_client=MagicMock(),
            config_store=_MockConfigStore(),
            script_repo=repo,
        )

        assert svc.find_scripts_by_nlp("unknown thing") == []
