"""Environment-variable-backed secret store for CI and integration testing.

Reads passwords from env vars instead of the OS keychain.
Never use this in production — it exposes secrets to any subprocess that inherits
the environment.

Supported env var patterns (checked in order):
  HAC_<ENV_NAME_UPPER>_PASSWORD   e.g. HAC_DEV_PASSWORD
  HAC_TEST_PASSWORD               generic fallback used in CI
"""

from __future__ import annotations

import os
from typing import Optional

from hac_cli.domain.ports import ISecretStore


class EnvSecretStore(ISecretStore):
    """Reads passwords from environment variables.

    For CI pipelines that cannot use OS keychain. Set the env var before running:
      export HAC_DEV_PASSWORD=secret && pytest tests/integration/
    """

    def get_password(self, env_name: str) -> Optional[str]:
        specific = os.getenv(f"HAC_{env_name.upper()}_PASSWORD")
        if specific:
            return specific
        return os.getenv("HAC_TEST_PASSWORD")

    def set_password(self, env_name: str, password: str) -> None:
        pass  # no-op — env vars cannot be set from within the process

    def delete_password(self, env_name: str) -> None:
        pass  # no-op
