"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from hac_cli.domain.models import Environment


@pytest.fixture
def dev_env() -> Environment:
    return Environment(
        name="dev",
        url="https://dev-hac.example.com",
        username="admin",
        timeout=30,
        verify_ssl=False,
    )


@pytest.fixture
def simple_groovy() -> str:
    return 'println "Hello from HAC"'
