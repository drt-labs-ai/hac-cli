"""Use case: execute a Groovy script on a HAC environment."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from hac_cli.domain.exceptions import (
    CommitBlockedBySafeModeError,
    EnvironmentNotFoundError,
    MissingCredentialsError,
)
from hac_cli.domain.models import ExecutionContext, ExecutionResult, ScriptMeta
from hac_cli.domain.ports import IConfigStore, IHacClient, IScriptRepository


class ExecuteGroovyService:
    def __init__(
        self,
        hac_client: IHacClient,
        config_store: IConfigStore,
        script_repo: IScriptRepository,
    ) -> None:
        self._client = hac_client
        self._config = config_store
        self._scripts = script_repo

    async def execute(
        self,
        env_name: str,
        file_path: Optional[Path] = None,
        script_library_path: Optional[str] = None,
        inline_code: Optional[str] = None,
        commit: bool = False,
    ) -> ExecutionResult:
        env = self._config.get_environment(env_name)
        if env is None:
            raise EnvironmentNotFoundError(env_name)

        if not env.password:
            raise MissingCredentialsError(env_name)

        if commit and env.safe_mode:
            raise CommitBlockedBySafeModeError(env_name)

        script_content = self._resolve_script(file_path, script_library_path, inline_code)

        ctx = ExecutionContext(
            environment=env,
            script_content=script_content,
            commit=commit,
        )
        return await self._client.execute(ctx)

    def find_scripts_by_nlp(self, query: str) -> list[ScriptMeta]:
        return self._scripts.search_scripts(query)

    def _resolve_script(
        self,
        file_path: Optional[Path],
        library_path: Optional[str],
        inline_code: Optional[str],
    ) -> str:
        if inline_code is not None:
            return inline_code
        if file_path is not None:
            return file_path.read_text(encoding="utf-8")
        if library_path is not None:
            return self._scripts.get_script_content(library_path)
        raise ValueError("No script source provided.")
