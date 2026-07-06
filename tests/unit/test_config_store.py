"""Unit tests for TomlConfigStore."""

from __future__ import annotations

import pytest

from hac_cli.domain.models import Environment
from hac_cli.infrastructure.config_store import TomlConfigStore


@pytest.fixture
def store(tmp_path):
    return TomlConfigStore(config_path=tmp_path / "config.toml")


def test_save_and_retrieve_environment(store):
    env = Environment(name="dev", url="https://dev.example.com", username="admin")
    store.save_environment(env)
    result = store.get_environment("dev")
    assert result is not None
    assert result.name == "dev"
    assert result.url == "https://dev.example.com"
    assert result.username == "admin"


def test_list_environments(store):
    store.save_environment(Environment(name="dev", url="https://dev.example.com", username="admin"))
    store.save_environment(Environment(name="staging", url="https://staging.example.com", username="admin"))
    envs = store.list_environments()
    assert len(envs) == 2
    names = {e.name for e in envs}
    assert names == {"dev", "staging"}


def test_delete_environment(store):
    env = Environment(name="dev", url="https://dev.example.com", username="admin")
    store.save_environment(env)
    store.delete_environment("dev")
    assert store.get_environment("dev") is None


def test_get_nonexistent_environment_returns_none(store):
    assert store.get_environment("nonexistent") is None


def test_overwrite_existing_environment(store):
    store.save_environment(Environment(name="dev", url="https://old.example.com", username="admin"))
    store.save_environment(Environment(name="dev", url="https://new.example.com", username="admin"))
    result = store.get_environment("dev")
    assert result is not None
    assert result.url == "https://new.example.com"
