"""Abstract ports (interfaces) — the dependency inversion boundary."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from hac_cli.domain.models import Environment, ExecutionContext, ExecutionResult, ScriptMeta


class IHacClient(ABC):
    @abstractmethod
    async def execute(self, ctx: ExecutionContext) -> ExecutionResult:
        ...

    @abstractmethod
    async def test_connection(self, env: Environment) -> bool:
        ...


class ISecretStore(ABC):
    @abstractmethod
    def get_password(self, env_name: str) -> Optional[str]:
        ...

    @abstractmethod
    def set_password(self, env_name: str, password: str) -> None:
        ...

    @abstractmethod
    def delete_password(self, env_name: str) -> None:
        ...


class IConfigStore(ABC):
    @abstractmethod
    def get_environment(self, name: str) -> Optional[Environment]:
        ...

    @abstractmethod
    def list_environments(self) -> list[Environment]:
        ...

    @abstractmethod
    def save_environment(self, env: Environment) -> None:
        ...

    @abstractmethod
    def delete_environment(self, name: str) -> None:
        ...


class IScriptRepository(ABC):
    @abstractmethod
    def list_scripts(self, category: Optional[str] = None) -> list[ScriptMeta]:
        ...

    @abstractmethod
    def get_script_content(self, path: str) -> str:
        ...

    @abstractmethod
    def search_scripts(self, query: str) -> list[ScriptMeta]:
        ...
