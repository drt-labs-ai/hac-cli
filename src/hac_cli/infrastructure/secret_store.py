"""OS keychain secret store via the keyring library."""

from __future__ import annotations

from typing import Optional

import keyring
import keyring.errors

from hac_cli.domain.ports import ISecretStore

_SERVICE_NAME = "hac-cli"


class KeyringSecretStore(ISecretStore):
    def get_password(self, env_name: str) -> Optional[str]:
        try:
            return keyring.get_password(_SERVICE_NAME, env_name)
        except keyring.errors.KeyringError:
            return None

    def set_password(self, env_name: str, password: str) -> None:
        keyring.set_password(_SERVICE_NAME, env_name, password)

    def delete_password(self, env_name: str) -> None:
        try:
            keyring.delete_password(_SERVICE_NAME, env_name)
        except keyring.errors.PasswordDeleteError:
            pass
