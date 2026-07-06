# Testing Patterns

## Mocking HAC HTTP (pytest-httpx)

```python
from pytest_httpx import HTTPXMock
from hac_cli.infrastructure.hac_client import HacHttpClient

LOGIN_HTML     = '<input type="hidden" name="_csrf" value="tok"/>'
SCRIPTING_HTML = '<meta name="_csrf" content="tok"/>'

@pytest.mark.asyncio
async def test_execute_success(httpx_mock: HTTPXMock, env):
    httpx_mock.add_response(method="GET",  url=env.login_page_url, text=LOGIN_HTML)
    httpx_mock.add_response(method="POST", url=env.login_url,
                            status_code=302, headers={"location": env.hac_base_url + "/"})
    httpx_mock.add_response(method="GET",  url=env.scripting_url, text=SCRIPTING_HTML)
    httpx_mock.add_response(method="POST", url=env.execute_url,
                            json={"executionResult": "ok", "stacktraceOccurred": False})

    client = HacHttpClient()
    result = await client.execute(ctx)
    assert result.succeeded
```

Register mocks in call order — pytest-httpx serves them sequentially.

## Injecting a pre-existing session (skip re-auth)

```python
from hac_cli.infrastructure.hac_client import _CachedSession
client._sessions["dev"] = _CachedSession(cookies={"JSESSIONID": "abc123"})
# Only CSRF fetch + execute are needed
```

## CLI tests (Typer CliRunner + env var injection)

```python
from typer.testing import CliRunner
from hac_cli.cli.app import build_app

runner = CliRunner()
app    = build_app()

def test_scripts_list(tmp_path):
    result = runner.invoke(app, ["scripts", "list"],
                           env={"HAC_SCRIPTS_PATH": str(tmp_path),
                                "HAC_CONFIG_PATH":  str(tmp_path)})
    assert result.exit_code == 0
```

## Mocking the application layer (AsyncMock)

```python
from unittest.mock import AsyncMock, MagicMock
from hac_cli.domain.ports import IHacClient

mock_client = MagicMock(spec=IHacClient)
mock_client.execute = AsyncMock(return_value=ExecutionResult(
    status=ExecutionStatus.SUCCESS, output="ok", execution_time_ms=42
))
```

## Environment fixture with safe_mode

Default `dev_env` has `safe_mode=True`. To test commit paths:

```python
env_no_safe = Environment(
    name="dev", url="https://dev.example.com",
    username="admin", password="secret", safe_mode=False,
)
```

## Integration tests (opt-in)

```python
import os, pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("HAC_TEST_URL"), reason="HAC_TEST_URL not set"
)
```

Required env vars: `HAC_TEST_URL`, `HAC_TEST_PASSWORD`.
Optional: `HAC_TEST_USER` (default `admin`), `HAC_TEST_VERIFY_SSL` (default `true`).

## Coverage thresholds

- ≥ 80% on `domain/` + `infrastructure/` layers
- CLI and TUI excluded from threshold
- Run with coverage: `uv run pytest tests/unit/ -v` (no `--no-cov`)
