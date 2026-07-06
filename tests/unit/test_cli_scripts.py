"""Integration tests for the hac scripts CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from hac_cli.cli.app import build_app

runner = CliRunner()
app = build_app()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def scripts_root(tmp_path: Path) -> Path:
    """A temporary script library with two categories."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "clear_all_caches.groovy").write_text(
        "// @meta\n"
        "// name: Clear All Caches\n"
        "// description: Clears all SAP Commerce cache regions\n"
        "// category: cache\n"
        "// tags: [cache, performance]\n"
        "// @end\n\n"
        'println "clearing"\n'
    )

    orders_dir = tmp_path / "orders"
    orders_dir.mkdir()
    (orders_dir / "get_order_status.groovy").write_text(
        "// @meta\n"
        "// name: Get Order Status\n"
        "// description: Retrieves order details by order code\n"
        "// category: orders\n"
        "// tags: [order, search]\n"
        "// @end\n\n"
        'println "order status"\n'
    )
    return tmp_path


def _invoke(args: list[str], scripts_root: Path) -> object:
    """Invoke the CLI with HAC_SCRIPTS_PATH set to the temp directory."""
    return runner.invoke(app, args, env={"HAC_SCRIPTS_PATH": str(scripts_root)})


# ---------------------------------------------------------------------------
# hac scripts list
# ---------------------------------------------------------------------------


class TestScriptsList:
    def test_list_shows_all_scripts(self, scripts_root: Path):
        result = _invoke(["scripts", "list"], scripts_root)
        assert result.exit_code == 0
        assert "Clear All Caches" in result.output
        assert "Get Order Status" in result.output

    def test_list_filter_by_category(self, scripts_root: Path):
        result = _invoke(["scripts", "list", "--category", "cache"], scripts_root)
        assert result.exit_code == 0
        assert "Clear All Caches" in result.output
        assert "Get Order Status" not in result.output

    def test_list_unknown_category_shows_no_cache_scripts(self, scripts_root: Path):
        result = _invoke(["scripts", "list", "--category", "nonexistent"], scripts_root)
        assert result.exit_code == 0
        assert "Clear All Caches" not in result.output


# ---------------------------------------------------------------------------
# hac scripts search
# ---------------------------------------------------------------------------


class TestScriptsSearch:
    def test_search_finds_cache_script(self, scripts_root: Path):
        result = _invoke(["scripts", "search", "cache clear"], scripts_root)
        assert result.exit_code == 0
        assert "Clear All Caches" in result.output

    def test_search_finds_order_script(self, scripts_root: Path):
        result = _invoke(["scripts", "search", "order status"], scripts_root)
        assert result.exit_code == 0
        assert "Get Order Status" in result.output

    def test_search_no_match_exits_0(self, scripts_root: Path):
        result = _invoke(["scripts", "search", "zzzzzznotfound"], scripts_root)
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# hac scripts show
# ---------------------------------------------------------------------------


class TestScriptsShow:
    def test_show_displays_groovy_source(self, scripts_root: Path):
        result = _invoke(["scripts", "show", "cache/clear_all_caches"], scripts_root)
        assert result.exit_code == 0
        assert "println" in result.output

    def test_show_nonexistent_exits_1(self, scripts_root: Path):
        result = _invoke(["scripts", "show", "cache/nonexistent"], scripts_root)
        assert result.exit_code == 1
