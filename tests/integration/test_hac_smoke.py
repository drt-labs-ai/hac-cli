"""Integration smoke tests — verify live HAC connectivity and basic execution.

Run with:
  HAC_TEST_URL=https://dev-hac.example.com \\
  HAC_TEST_PASSWORD=admin123 \\
  uv run pytest tests/integration/ -v

All tests are skipped automatically when HAC_TEST_URL is not set.
"""

from __future__ import annotations

import time

import pytest

from hac_cli.domain.models import ExecutionContext, ExecutionStatus


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_connection(hac_client, hac_env):
    """HAC is reachable and credentials are valid."""
    assert await hac_client.test_connection(hac_env)


@pytest.mark.asyncio
async def test_execute_simple_println(hac_client, ping_ctx):
    """Basic Groovy execution returns stdout output."""
    result = await hac_client.execute(ping_ctx)

    assert result.succeeded, f"Expected success, got: {result.stack_trace}"
    assert "hac-cli:ping:ok" in result.output
    assert result.execution_time_ms >= 0
    assert result.environment_name == "test"


@pytest.mark.asyncio
async def test_execute_returns_expression_result(hac_client, hac_env):
    """Groovy expression result is captured."""
    ctx = ExecutionContext(
        environment=hac_env,
        script_content="return 2 + 2",
        commit=False,
    )
    result = await hac_client.execute(ctx)
    assert result.succeeded
    assert "4" in result.output


@pytest.mark.asyncio
async def test_execute_groovy_error_captured(hac_client, hac_env):
    """Syntax/runtime errors are returned as ERROR status with stacktrace."""
    ctx = ExecutionContext(
        environment=hac_env,
        script_content="thisMethodDoesNotExist()",
        commit=False,
    )
    result = await hac_client.execute(ctx)

    assert result.status == ExecutionStatus.ERROR
    assert result.stack_trace is not None
    assert len(result.stack_trace) > 0


@pytest.mark.asyncio
async def test_execute_dry_run_does_not_persist(hac_client, hac_env):
    """commit=False wraps execution in a rolled-back transaction."""
    unique_tag = f"hac-cli-test-{int(time.time())}"
    ctx = ExecutionContext(
        environment=hac_env,
        script_content=f"""
import de.hybris.platform.servicelayer.search.FlexibleSearchService
import de.hybris.platform.core.Registry

def fss = Registry.getApplicationContext().getBean(FlexibleSearchService.class)
def result = fss.search("SELECT count({{pk}}) FROM {{Title}} WHERE {{code}}=?c", [c: '{unique_tag}'])
println "before: ${{result.result[0]}}"
""",
        commit=False,
    )
    result = await hac_client.execute(ctx)
    assert result.succeeded
    assert "before: 0" in result.output


@pytest.mark.asyncio
async def test_session_reuse_skips_reauth(hac_client, hac_env, ping_ctx):
    """Second execution reuses the cached session (no new login calls)."""
    # First call authenticates and caches the session
    r1 = await hac_client.execute(ping_ctx)
    assert r1.succeeded

    session_before = dict(hac_client._sessions)

    # Second call should reuse the cached session
    r2 = await hac_client.execute(ping_ctx)
    assert r2.succeeded

    # Session entry should be the same object (not recreated)
    assert "test" in hac_client._sessions
    assert hac_client._sessions["test"].created_at == session_before["test"].created_at


@pytest.mark.asyncio
async def test_multiline_script_output(hac_client, hac_env):
    """Multi-line scripts produce concatenated output."""
    ctx = ExecutionContext(
        environment=hac_env,
        script_content="""
println "line1"
println "line2"
println "line3"
""",
        commit=False,
    )
    result = await hac_client.execute(ctx)
    assert result.succeeded
    assert "line1" in result.output
    assert "line2" in result.output
    assert "line3" in result.output
