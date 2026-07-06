"""Integration test fixtures — require a live SAP Commerce HAC instance.

All integration tests are automatically skipped when HAC_TEST_URL is not set.

Required env vars:
  HAC_TEST_URL          Full HAC base URL, e.g. https://dev-hac.example.com
  HAC_TEST_PASSWORD     Admin password (or HAC_TEST_PASSWORD for the env named "test")

Optional env vars:
  HAC_TEST_USER         Admin username (default: admin)
  HAC_TEST_VERIFY_SSL   true/false (default: true)
"""

from __future__ import annotations

import os

import pytest

from hac_cli.domain.models import Environment, ExecutionContext
from hac_cli.infrastructure.env_secret_store import EnvSecretStore
from hac_cli.infrastructure.hac_client import HacHttpClient


def _require_hac_url() -> str:
    url = os.getenv("HAC_TEST_URL")
    if not url:
        pytest.skip("HAC_TEST_URL not set — skipping integration tests")
    return url


@pytest.fixture(scope="session")
def hac_env() -> Environment:
    return Environment(
        name="test",
        url=_require_hac_url(),
        username=os.getenv("HAC_TEST_USER", "admin"),
        timeout=int(os.getenv("HAC_TEST_TIMEOUT", "60")),
        verify_ssl=os.getenv("HAC_TEST_VERIFY_SSL", "true").lower() != "false",
    )


@pytest.fixture(scope="session")
def hac_client() -> HacHttpClient:
    return HacHttpClient(secret_store=EnvSecretStore())


@pytest.fixture
def ping_ctx(hac_env: Environment) -> ExecutionContext:
    return ExecutionContext(
        environment=hac_env,
        script_content='println "hac-cli:ping:ok"',
        commit=False,
    )
