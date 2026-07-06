# CLAUDE.md — hac-cli Development Guide

This file is the authoritative guide for AI-assisted development on this project.
Read it before making any changes.

## Project Overview

**hac-cli** is a Python CLI tool that automates execution of HAC (Hybris Administration Console)
Groovy scripts across SAP Commerce environments. It eliminates browser-based HAC usage for
routine operations.

**Key entry point:** `src/hac_cli/main.py` → `src/hac_cli/cli/app.py`

## Architecture

```
CLI (Typer)  →  Application (Use Cases)  →  Domain (Models + Ports)
                                         ↑
                          Infrastructure (Adapters) implements Ports
```

### Layer Rules

| Layer | Location | Rule |
|---|---|---|
| CLI | `src/hac_cli/cli/` | Only Typer commands + Rich output. No business logic. |
| Application | `src/hac_cli/application/` | Orchestrates domain + infrastructure via ports. No HTTP. |
| Domain | `src/hac_cli/domain/` | Pure Python. Zero external imports. |
| Infrastructure | `src/hac_cli/infrastructure/` | All external I/O. Implements domain ports. |

**Never** import infrastructure directly from CLI. CLI → Application → Infrastructure (via ports).

## Security Rules — MANDATORY

1. **No secrets on disk.** Passwords/tokens go to `KeyringSecretStore` only.
2. **No secrets in logs.** All output passes through `utils/logging.redact()`.
3. **No secrets in `.gitignore`-covered files.** The `detect-secrets` baseline enforces this.
4. **SSL verify=True by default.** Only disable with explicit `--no-ssl-verify` flag.
5. **Never commit** files matching: `*.env`, `*.key`, `secrets.*`, `config.local.*`, `cookies.txt`.
6. **CSRF token handling** — always fetch fresh token before each execution; never cache it.

If you see a secret pattern (password=, token=, Authorization:) in code you're about to write, stop and use the secret store instead.

## Development Workflows

### Adding a New Environment Command
1. Add the command to `src/hac_cli/cli/cmd_env.py`
2. If it needs new logic, add a method to `application/manage_environments.py`
3. If it needs new infrastructure, add to `infrastructure/config_store.py` or `infrastructure/secret_store.py`
4. Add unit tests in `tests/unit/`

### Adding a New Script to the Library
1. Create `scripts/<category>/<name>.groovy`
2. Add `// @meta ... // @end` frontmatter (see `scripts/_templates/script.groovy.template`)
3. Test with `hac scripts show <category>/<name>`

### Adding a New CLI Subcommand Group
1. Create `src/hac_cli/cli/cmd_<name>.py` with `<name>_app = typer.Typer(...)`
2. Register in `src/hac_cli/cli/app.py` via `app.add_typer(...)`
3. Add use case in `application/`

### HAC Client Changes (Phase 3+)
The `HacHttpClient` in `infrastructure/hac_client.py` implements `IHacClient`.
Auth flow: login → get CSRF → execute → parse response.
Never cache CSRF tokens across sessions.

## Coding Standards

### Python
- Python 3.11+ — use `match`, `tomllib`, `datetime.UTC`, `X | Y` union types
- Type hints on all public functions — `mypy --strict` must pass
- `ruff` for linting and formatting (replaces black + isort + flake8)
- Dataclasses or Pydantic for models — no raw dicts passed between layers
- `from __future__ import annotations` in all files
- No comments on obvious code. Comments only for non-obvious WHY.

### Groovy Scripts
- Always use `binding.hasVariable("param")` guard before accessing script params
- Get Spring beans via `Registry.getApplicationContext().getBean(...)`
- Always print clear output — HAC returns stdout as the result
- Handle nulls explicitly — SAP Commerce objects are often nullable

### Testing
- Unit tests: `tests/unit/` — mock all I/O via pytest fixtures
- Integration tests: `tests/integration/` — require `HAC_TEST_URL` env var, skipped in CI unless set
- Coverage threshold: 80% for unit tests
- Use `pytest-httpx` for mocking httpx in client tests

## Common Prompts for Claude

### "Add FlexibleSearch support"
Create `src/hac_cli/cli/cmd_flexsearch.py`, `application/execute_flexsearch.py`.
Reuse `IHacClient` — FlexibleSearch has its own HAC endpoint: `/console/flexiblesearch/api/execute`.
Follow the same pattern as `cmd_groovy.py`.

### "Add ImpEx import support"
HAC ImpEx endpoint: `POST /console/impex/import`. Add `IHacImpExClient` port.
Implement in `infrastructure/hac_impex_client.py`.

### "Add parallel execution"
`ExecuteGroovyService.execute_many(envs, script)` → `asyncio.gather(...)`.
Add `--env` as multi-value option: `--env dev --env staging`.

### "Add NLP/Claude API script selection"
Replace fuzzy search in `nlp_selector.py` with `anthropic.Anthropic().messages.create(...)`.
Use model `claude-haiku-4-5-20251001` for speed. Prompt: classify query to script name.

### "Publish to PyPI"
Update version in `pyproject.toml`, update `CHANGELOG.md`, tag `v{version}`, push tag.
GitHub Actions `release.yml` handles the rest.

## File Map

```
src/hac_cli/
  main.py                  # Entry point
  cli/app.py               # Root Typer app + subcommand registration
  cli/cmd_env.py           # hac env *
  cli/cmd_groovy.py        # hac groovy *
  cli/cmd_scripts.py       # hac scripts *
  application/
    manage_environments.py # EnvironmentService
    execute_groovy.py      # ExecuteGroovyService
  domain/
    models.py              # Environment, ExecutionContext, ExecutionResult, ScriptMeta
    ports.py               # IHacClient, ISecretStore, IConfigStore, IScriptRepository
    exceptions.py          # All domain exceptions
  infrastructure/
    hac_client.py          # HAC HTTP (Phase 3)
    secret_store.py        # OS keychain via keyring
    config_store.py        # ~/.hac-cli/config.toml
    script_repository.py   # Filesystem script library + fuzzy search
  tui/app.py               # Textual TUI (Phase 4)
  utils/
    logging.py             # Secret-redacting logger
    output.py              # Rich console helpers

scripts/                   # Groovy script library
  cache/                   # Cache management
  catalog/                 # Catalog operations
  customer/                # Customer queries
  orders/                  # Order management
  _templates/              # Script authoring template

tests/
  unit/                    # Fast, no I/O, no HAC
  integration/             # Requires live HAC (opt-in)
  conftest.py              # Shared fixtures
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `HAC_CONFIG_PATH` | Override `~/.hac-cli/config.toml` path |
| `HAC_TEST_URL` | Enable integration tests against a live HAC |
| `HAC_LOG_LEVEL` | Log level: DEBUG, INFO, WARNING (default: WARNING) |

## What NOT to do

- Don't store credentials in config files — use `KeyringSecretStore`
- Don't bypass SSL verification in non-dev environments
- Don't add `print()` statements — use `utils/output.py` helpers or the logger
- Don't import from `infrastructure` in `domain` — direction is domain → infrastructure via ports
- Don't hardcode environment URLs or usernames in tests — use fixtures from `conftest.py`
- Don't add `# type: ignore` without a comment explaining why
