"""TOML-based config store for environment metadata (no secrets)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Optional

import tomli_w

from hac_cli.domain.models import Environment
from hac_cli.domain.ports import IConfigStore

_CONFIG_DIR = Path.home() / ".hac-cli"
_CONFIG_FILE = _CONFIG_DIR / "config.toml"


class TomlConfigStore(IConfigStore):
    def __init__(self, config_path: Path = _CONFIG_FILE) -> None:
        self._path = config_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        with self._path.open("rb") as f:
            return tomllib.load(f)

    def _save(self, data: dict) -> None:
        with self._path.open("wb") as f:
            tomli_w.dump(data, f)

    def get_environment(self, name: str) -> Optional[Environment]:
        data = self._load()
        envs = data.get("environments", {})
        if name not in envs:
            return None
        return self._dict_to_env(name, envs[name])

    def list_environments(self) -> list[Environment]:
        data = self._load()
        envs = data.get("environments", {})
        return [self._dict_to_env(name, cfg) for name, cfg in envs.items()]

    def save_environment(self, env: Environment) -> None:
        data = self._load()
        data.setdefault("environments", {})[env.name] = {
            "url": env.url,
            "username": env.username,
            "timeout": env.timeout,
            "verify_ssl": env.verify_ssl,
        }
        self._save(data)

    def delete_environment(self, name: str) -> None:
        data = self._load()
        data.get("environments", {}).pop(name, None)
        self._save(data)

    @staticmethod
    def _dict_to_env(name: str, cfg: dict) -> Environment:
        return Environment(
            name=name,
            url=cfg["url"],
            username=cfg["username"],
            timeout=cfg.get("timeout", 30),
            verify_ssl=cfg.get("verify_ssl", True),
        )
