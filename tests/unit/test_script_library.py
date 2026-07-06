"""Unit tests for FilesystemScriptRepository."""

from __future__ import annotations

from pathlib import Path

import pytest

from hac_cli.infrastructure.script_repository import FilesystemScriptRepository


@pytest.fixture
def scripts_dir(tmp_path: Path) -> Path:
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    script = cache_dir / "clear_all_caches.groovy"
    script.write_text(
        """// @meta
// name: Clear All Caches
// description: Clears all SAP Commerce cache regions
// category: cache
// tags: [cache, performance]
// @end

import de.hybris.platform.cache.Cache
println "clearing caches"
"""
    )

    plain = cache_dir / "plain_script.groovy"
    plain.write_text('println "no meta"')

    return tmp_path


@pytest.fixture
def repo(scripts_dir: Path) -> FilesystemScriptRepository:
    return FilesystemScriptRepository(scripts_root=scripts_dir)


def test_list_scripts_returns_all(repo):
    scripts = repo.list_scripts()
    assert len(scripts) == 2


def test_list_scripts_by_category(repo):
    scripts = repo.list_scripts(category="cache")
    assert all(s.category == "cache" for s in scripts)


def test_parse_meta_from_frontmatter(repo):
    scripts = repo.list_scripts()
    meta_script = next(s for s in scripts if s.name == "Clear All Caches")
    assert meta_script.description == "Clears all SAP Commerce cache regions"
    assert "cache" in meta_script.tags
    assert "performance" in meta_script.tags


def test_get_script_content(repo, scripts_dir):
    content = repo.get_script_content("cache/clear_all_caches")
    assert "println" in content


def test_get_script_raises_for_missing(repo):
    with pytest.raises(FileNotFoundError):
        repo.get_script_content("cache/nonexistent")


def test_search_scripts_fuzzy(repo):
    results = repo.search_scripts("cache clear")
    assert len(results) >= 1


def test_search_scripts_no_match(repo):
    results = repo.search_scripts("xxxxxxxx")
    assert results == []
