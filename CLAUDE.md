# CLAUDE.md — hac-cli Development Guide

This file is the authoritative guide for AI-assisted development on this project.
**Read it in full before making any changes.**

---

## Project Overview

**hac-cli** is a Python 3.11+ CLI/TUI tool that automates execution of HAC
(Hybris Administration Console) Groovy scripts across SAP Commerce environments
without opening a browser.

**Entry point:** `src/hac_cli/main.py` → `cli/app.py`
**Interactive TUI:** `tui/app.py` (Textual)

---

## Phase Completion Status

| Phase | Status | Key deliverable |
|---|---|---|
| 1 — Architecture & Design | ✅ Done | Stack choice, layer map, security model |
| 2 — Repository Bootstrap | ✅ Done | 51-file skeleton, domain models, ports, CI/CD |
| 3 — HAC Auth & Execution | ✅ Done | `HacHttpClient` — login, CSRF, execute, re-auth |
| 4 — CLI/TUI & Script Library | ✅ Done | Textual TUI, CLI tests, env-var testability |
| 5 — Claude Configuration | ✅ Done | This file, hooks, MCP, docs |
| 6 — Testing, Docs, Packaging | ⬜ Next | Integration tests, PyPI, release automation |

---

## Architecture

```
CLI (Typer)  →  Application (Use Cases)  →  Domain (Models + Ports)
TUI (Textual) →                           ←  Infrastructure (Adapters)
```

### Layer Rules

| Layer | Location | Rule |
|---|---|---|
| CLI | `src/hac_cli/cli/` | Typer commands + Rich output only. No business logic. |
| Application | `src/hac_cli/application/` | Orchestrates ports. No HTTP. No OS I/O. |
| Domain | `src/hac_cli/domain/` | Pure Python. Zero external imports. Frozen dataclasses. |
| Infrastructure | `src/hac_cli/infrastructure/` | All external I/O. Implements domain ports. |
| TUI | `src/hac_cli/tui/` | Textual App. Calls Application layer only. |

**Never** import infrastructure directly from CLI or TUI.
**Never** import anything from `infrastructure` inside `domain`.

---

## Security Rules — MANDATORY

1. **No secrets on disk.** Passwords/tokens → `KeyringSecretStore` only.
2. **No secrets in logs.** All output through `utils/logging.redact()`.
3. **SSL verify=True by default.** Only `--no-ssl-verify` overrides it (dev only).
4. **CSRF tokens are never cached.** Fetch fresh on every execute call.
5. **Never stage** `*.env`, `*.key`, `secrets.*`, `config.local.*`, `cookies.txt`.
6. **Never use `print()`** in source. Use `utils/output.py` or the logger.
7. **Never hardcode** environment URLs, usernames, or passwords in tests.

The `.claude/hooks/pre_tool_call.py` enforces rules 1 and 5 at tool-call time.

---

## HAC API Quick Reference

| Step | Method | URL | Notes |
|---|---|---|---|
| Login page | GET | `/login` | Extract `<input name="_csrf">` |
| Authenticate | POST | `/j_spring_security_check` | `j_username`, `j_password`, `_csrf`; `follow_redirects=False` |
| CSRF for scripts | GET | `/console/scripting/api/` | Extract `<meta name="_csrf" content="...">` |
| Execute Groovy | POST | `/console/scripting/api/execute` | Form body: `script`, `commit`; Header: `X-CSRF-TOKEN` |
| FlexibleSearch | POST | `/console/flexiblesearch/api/execute` | Same auth pattern |
| ImpEx import | POST | `/console/impex/import` | Multipart or form body |

**Response format for Groovy execution:**
```json
{
  "executionResult": "output or stacktrace",
  "stacktraceOccurred": false,
  "outputText": "stdout output (newer SAP Commerce versions)"
}
```

Login success = 302 to `/` or app root.
Login failure = 302 to `/login?error=true`.
Session expired = CSRF-page GET redirects to `/login`.

---

## File Map

```
src/hac_cli/
  main.py                    Entry point
  cli/
    app.py                   Root Typer app + subcommand registration
    cmd_env.py               hac env add/list/remove/test
    cmd_groovy.py            hac groovy run/exec
    cmd_scripts.py           hac scripts list/search/show
  application/
    execute_groovy.py        ExecuteGroovyService — resolves script, calls client
    manage_environments.py   EnvironmentService — CRUD + credential delegation
  domain/
    models.py                Environment, ExecutionContext, ExecutionResult, ScriptMeta
    ports.py                 IHacClient, ISecretStore, IConfigStore, IScriptRepository
    exceptions.py            6 typed exceptions (all extend HacCliError)
  infrastructure/
    hac_client.py            HacHttpClient — auth + CSRF + execute + session cache
    secret_store.py          KeyringSecretStore — OS keychain
    config_store.py          TomlConfigStore — ~/.hac-cli/config.toml
    script_repository.py     FilesystemScriptRepository — glob + frontmatter + fuzzy search
  tui/
    app.py                   HacApp (Textual) — script browser + env switcher + output log
    widgets.py               ScriptInfoBar, OutputPanel helpers
  utils/
    logging.py               RedactingFilter + get_logger()
    output.py                Rich console helpers (print_success/error/warning/info)

scripts/                     Groovy script library (categorised)
  cache/                     clear_all_caches, clear_region
  catalog/                   get_catalog_versions, sync_catalog
  customer/                  find_customer
  orders/                    get_order_status
  _templates/                script.groovy.template

tests/
  unit/                      Fast, no I/O — 65 tests, 91% coverage
    test_config_store.py
    test_hac_client.py       34 tests with pytest-httpx mocking
    test_execute_groovy.py   11 tests with MagicMock/AsyncMock
    test_cli_scripts.py      8 tests via Typer CliRunner + HAC_SCRIPTS_PATH
    test_script_library.py
  integration/               Opt-in, requires HAC_TEST_URL
  conftest.py                Shared fixtures: dev_env, simple_groovy

docs/
  architecture.md            Layer diagrams, auth flow, extension points
  getting-started.md         Installation, configuration, common workflows
  security.md                Credential storage, secret scanning, transport security
  script-authoring.md        Frontmatter format, Spring beans, Groovy patterns
```

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `HAC_CONFIG_PATH` | `~/.hac-cli` | Override config directory (evaluated at instantiation) |
| `HAC_SCRIPTS_PATH` | `<repo>/scripts` | Override script library root (evaluated at instantiation) |
| `HAC_LOG_LEVEL` | `WARNING` | Log level: DEBUG, INFO, WARNING |
| `HAC_TEST_URL` | (unset) | Live HAC URL — activates integration tests |

---

## Development Workflows

### Add a new Groovy script to the library
1. Create `scripts/<category>/<name>.groovy`
2. Add `// @meta … // @end` frontmatter (copy `scripts/_templates/script.groovy.template`)
3. Test: `hac scripts show <category>/<name>`
4. Dry-run: `hac groovy run --env dev --script <category>/<name>`

### Add a new CLI subcommand group
1. Create `src/hac_cli/cli/cmd_<name>.py` with `<name>_app = typer.Typer(...)`
2. Register in `cli/app.py` via `app.add_typer(<name>_app, name="<name>", help="...")`
3. Add use case in `application/<name>.py`
4. Add unit tests in `tests/unit/test_cli_<name>.py` using `CliRunner` + env var injection

### Add a new environment config field
1. Add field to `domain/models.py` `Environment` dataclass (with default)
2. Serialize/deserialize in `infrastructure/config_store.py` `_dict_to_env` and `save_environment`
3. Expose via `hac env add --new-flag` in `cli/cmd_env.py`

### Add a TUI widget or screen
1. Add Textual widget to `tui/widgets.py` or a new `tui/<screen>.py`
2. Import and compose in `tui/app.py`
3. Add reactive property if the widget responds to app state
4. Wire keyboard binding in `BINDINGS` list

### Run tests
```bash
uv run pytest tests/unit/ -v                    # unit tests + coverage
uv run pytest tests/unit/ -v --no-cov           # fast, no coverage overhead
uv run pytest tests/unit/test_hac_client.py -v  # single file
HAC_TEST_URL=https://dev-hac.example.com uv run pytest tests/integration/  # integration
```

### Check code quality
```bash
uv run ruff check src/ tests/    # lint
uv run ruff format src/ tests/   # format
uv run mypy src/                 # type check
```

---

## Testing Patterns

### Mocking HAC HTTP with pytest-httpx

```python
from pytest_httpx import HTTPXMock
from hac_cli.infrastructure.hac_client import HacHttpClient

@pytest.mark.asyncio
async def test_execute_success(httpx_mock: HTTPXMock, env):
    # Register mocks in call order
    httpx_mock.add_response(method="GET",  url=env.login_page_url, text=LOGIN_HTML)
    httpx_mock.add_response(method="POST", url=env.login_url,
                            status_code=302, headers={"location": env.hac_base_url + "/"})
    httpx_mock.add_response(method="GET",  url=env.scripting_url, text=SCRIPTING_HTML)
    httpx_mock.add_response(method="POST", url=env.execute_url,
                            json={"executionResult": "ok", "stacktraceOccurred": False})

    client = HacHttpClient(secret_store=mock_store)
    result = await client.execute(ctx)
    assert result.succeeded
```

HTML snippets to re-use:
```python
LOGIN_HTML    = '<input type="hidden" name="_csrf" value="tok"/>'
SCRIPTING_HTML = '<meta name="_csrf" content="tok"/>'
```

### Injecting a pre-existing session (skip re-auth)

```python
from hac_cli.infrastructure.hac_client import _CachedSession
client._sessions["dev"] = _CachedSession(cookies={"JSESSIONID": "abc123"})
# Now only CSRF fetch + execute are needed
```

### CLI tests with env var injection

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

### Mocking the application layer with AsyncMock

```python
from unittest.mock import AsyncMock, MagicMock
from hac_cli.domain.ports import IHacClient

mock_client = MagicMock(spec=IHacClient)
mock_client.execute = AsyncMock(return_value=ExecutionResult(
    status=ExecutionStatus.SUCCESS, output="ok", execution_time_ms=42
))
```

---

## Common Claude Prompts

### "Add FlexibleSearch command"
```
Create src/hac_cli/cli/cmd_flexsearch.py with Typer commands:
  hac fs query --env dev --query "SELECT {pk} FROM {Product}"
  hac fs query --env dev --file my_query.fxs

HAC FlexibleSearch endpoint:
  POST /console/flexiblesearch/api/execute
  Body (form): flexibleSearchQuery=<query>, maxCount=200, itemsPerPage=20
  Response: { "query": {...}, "exception": null, "resultList": [...] }

Reuse HacHttpClient — add execute_flexsearch() method that:
1. Calls _ensure_authenticated() + _fetch_csrf_token() (same as Groovy)
2. POSTs to /console/flexiblesearch/api/execute
3. Returns a FlexSearchResult model with headers + rows

Add application/execute_flexsearch.py FlexSearchService following the same
pattern as execute_groovy.py. Register in cli/app.py.
```

### "Add ImpEx import command"
```
Create src/hac_cli/cli/cmd_impex.py:
  hac impex import --env dev --file data.impex
  hac impex import --env dev --inline "INSERT_UPDATE Product;code[unique=true];name"

HAC ImpEx endpoint:
  POST /console/impex/import
  Body (form): scriptContent=<impex>, validationEnum=IMPORT_STRICT,
               maxThreads=1, encoding=UTF-8, _legacyMode=false
  Response: HTML page — check for "Import finished" vs error div

Add ImpexResult domain model. Parse the HTML response for
success/error indicators (BeautifulSoup).
```

### "Add parallel execution across environments"
```
Add to ExecuteGroovyService:
  async def execute_many(self, env_names: list[str], ...) -> list[ExecutionResult]:
      tasks = [self.execute(env_name=e, ...) for e in env_names]
      return await asyncio.gather(*tasks, return_exceptions=True)

Update cmd_groovy.py run command:
  --env can be specified multiple times:
  @groovy_app.command()
  def run(env: list[str] = typer.Option(..., "--env", "-e"), ...)

Display results in a Rich Table with per-env status column.
```

### "Add Claude API NLP script selection"
```
In application/execute_groovy.py, update find_scripts_by_nlp():
  from anthropic import Anthropic
  client = Anthropic()
  scripts = self._scripts.list_scripts()
  script_list = "\n".join(f"{s.path}: {s.description}" for s in scripts)
  msg = client.messages.create(
      model="claude-haiku-4-5-20251001",
      max_tokens=100,
      messages=[{"role": "user", "content":
          f"From this list:\n{script_list}\n\n"
          f"Which script best matches: '{query}'?\n"
          "Reply with just the path, e.g. cache/clear_all_caches"}],
  )
  path = msg.content[0].text.strip()
  return [s for s in scripts if s.path == path]

Add anthropic>=0.30 to pyproject.toml dependencies.
```

### "Add integration test for hac groovy run"
```
In tests/integration/test_hac_groovy.py:
  import pytest, os
  pytestmark = pytest.mark.skipif(
      not os.getenv("HAC_TEST_URL"), reason="HAC_TEST_URL not set"
  )

  @pytest.mark.asyncio
  async def test_execute_inline_on_live_hac(hac_env):
      # hac_env fixture from conftest: reads HAC_TEST_URL + HAC_TEST_USER
      client = HacHttpClient(secret_store=EnvSecretStore())
      ctx = ExecutionContext(environment=hac_env, script_content='println "ping"')
      result = await client.execute(ctx)
      assert result.succeeded
      assert "ping" in result.output
```

### "Release a new version"
```
1. Update version in pyproject.toml: version = "X.Y.Z"
2. Update CHANGELOG.md — move Unreleased → [X.Y.Z] with today's date
3. Run: uv run pytest tests/unit/ && uv run ruff check src/
4. git add pyproject.toml CHANGELOG.md && git commit -m "chore: release vX.Y.Z"
5. git tag vX.Y.Z && git push && git push --tags
6. GitHub Actions release.yml handles PyPI publish + GitHub Release automatically
```

### "Debug a HAC authentication failure"
```
Enable debug logging:
  HAC_LOG_LEVEL=DEBUG hac env test dev 2>&1 | head -50

Check that:
1. URL is reachable: curl -v https://your-hac/login
2. Login redirect location does NOT contain "error"
3. Scripting page responds with 200 and contains <meta name="_csrf">

To dump raw HTTP: add httpx event hooks temporarily to HacHttpClient._make_client():
  event_hooks={"request": [lambda r: print(r.url)],
               "response": [lambda r: print(r.status_code, r.url)]}
```

---

## Coding Standards

### Python
- Python 3.11+ syntax: `match`, `tomllib`, `X | Y` unions, `datetime.now(timezone.utc)`
- `from __future__ import annotations` in every source file
- Type hints on all public functions; `mypy --strict` must pass
- `ruff` for linting and formatting — no separate black/isort/flake8
- Frozen dataclasses for value objects; unfrozen for mutable results
- No comments on obvious code — only non-obvious WHY
- No `# type: ignore` without an explanatory comment

### Groovy scripts
- `binding.hasVariable("param")` guard on every parameter
- Beans via `Registry.getApplicationContext().getBean(Type.class)` (type-safe)
- Always `println` a meaningful result — HAC returns stdout as the output
- Null-safe navigation: `order?.user?.uid ?: "(unknown)"`

### Tests
- `tests/unit/` — fast, no external I/O; all HTTP mocked via `pytest-httpx`
- `tests/integration/` — opt-in, gate with `pytestmark = pytest.mark.skipif(not os.getenv("HAC_TEST_URL")...)`
- Coverage ≥ 80% on domain + infrastructure layers (CLI/TUI excluded from threshold)
- Fixtures in `conftest.py` — no hardcoded URLs or credentials anywhere in test files

---

## What NOT to do

| Don't | Do instead |
|---|---|
| Store credentials in config file | `KeyringSecretStore.set_password()` |
| `print()` in source | `utils/output.print_*()` or logger |
| Import infrastructure in domain | Use ports (abstract base classes) |
| Hardcode env URLs/passwords in tests | Use `conftest.py` fixtures + env vars |
| Add `# type: ignore` silently | Comment explaining the unavoidable reason |
| Bypass SSL in non-dev envs | Keep `verify_ssl=True`; fix the cert instead |
| Cache CSRF tokens | Fetch fresh on every execute call |
| Add `uv run pip install` | Add to `pyproject.toml` and run `uv sync` |
