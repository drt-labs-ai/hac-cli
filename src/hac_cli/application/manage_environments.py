"""Use case: manage environment configurations."""

from __future__ import annotations

from typing import Optional

from hac_cli.domain.exceptions import EnvironmentNotFoundError
from hac_cli.domain.models import Environment
from hac_cli.domain.ports import IConfigStore


class EnvironmentService:
    def __init__(self, config_store: IConfigStore) -> None:
        self._config = config_store

    def add_environment(
        self,
        name: str,
        url: str,
        username: str,
        password: str,
        timeout: int = 30,
        verify_ssl: bool = True,
        safe_mode: bool = True,
    ) -> Environment:
        env = Environment(
            name=name,
            url=url,
            username=username,
            password=password,
            timeout=timeout,
            verify_ssl=verify_ssl,
            safe_mode=safe_mode,
        )
        self._config.save_environment(env)
        return env

    def remove_environment(self, name: str) -> None:
        env = self._config.get_environment(name)
        if env is None:
            raise EnvironmentNotFoundError(name)
        self._config.delete_environment(name)

    def get_environment(self, name: str) -> Optional[Environment]:
        return self._config.get_environment(name)

    def list_environments(self) -> list[Environment]:
        return self._config.list_environments()
