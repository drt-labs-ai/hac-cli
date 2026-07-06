"""HAC HTTP client — handles auth, CSRF, and script execution.

NOTE: Full implementation is Phase 3. This is a typed placeholder that satisfies
the IHacClient port so the rest of the codebase compiles and tests run.
"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from hac_cli.domain.exceptions import HacAuthenticationError, HacConnectionError
from hac_cli.domain.models import Environment, ExecutionContext, ExecutionResult, ExecutionStatus
from hac_cli.domain.ports import IHacClient, ISecretStore


class HacHttpClient(IHacClient):
    """Full implementation delivered in Phase 3."""

    def __init__(self, secret_store: ISecretStore) -> None:
        self._secrets = secret_store

    async def execute(self, ctx: ExecutionContext) -> ExecutionResult:
        raise NotImplementedError("HacHttpClient.execute — implemented in Phase 3")

    async def test_connection(self, env: Environment) -> bool:
        raise NotImplementedError("HacHttpClient.test_connection — implemented in Phase 3")
