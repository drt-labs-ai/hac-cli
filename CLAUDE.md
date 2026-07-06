# CLAUDE.md — hac-cli

**hac-cli** — Python 3.11+ CLI/TUI for executing HAC Groovy scripts across SAP Commerce environments.
Entry point: `src/hac_cli/main.py` → `cli/app.py` | TUI: `tui/app.py`

---

## Phase Status

| Phase | Status | Deliverable |
|---|---|---|
| 1 — Architecture & Design | ✅ Done | Stack, layer map, security model |
| 2 — Repository Bootstrap  | ✅ Done | 51-file skeleton, domain models, ports, CI/CD |
| 3 — HAC Auth & Execution  | ✅ Done | `HacHttpClient` — login, CSRF, execute, re-auth |
| 4 — CLI/TUI & Script Library | ✅ Done | Textual TUI, CLI tests, env-var testability |
| 5 — Claude Configuration  | ✅ Done | CLAUDE.md, hooks, rules, docs |
| 6 — Testing, Docs, Packaging | ✅ Done | Integration tests, PyPI, release automation |

---

## Architecture

```
CLI (Typer)  →  Application (Use Cases)  →  Domain (Models + Ports)
TUI (Textual) →                           ←  Infrastructure (Adapters)
```

| Layer | Location | Rule |
|---|---|---|
| CLI | `src/hac_cli/cli/` | Typer + Rich only. No business logic. |
| Application | `src/hac_cli/application/` | Orchestrates ports. No HTTP. No OS I/O. |
| Domain | `src/hac_cli/domain/` | Pure Python. Zero external imports. Frozen dataclasses. |
| Infrastructure | `src/hac_cli/infrastructure/` | All external I/O. Implements domain ports. |
| TUI | `src/hac_cli/tui/` | Textual App. Calls Application layer only. |

**Never** import infrastructure from CLI or TUI. **Never** import infrastructure inside domain.

---

## Security Rules — MANDATORY

1. **Passwords in `config.toml` (project root).** Gitignored — never commit it.
2. **No secrets in logs.** All output through `utils/logging.redact()`.
3. **SSL `verify=True` by default.** Only `--no-ssl-verify` overrides it (dev only).
4. **CSRF tokens never cached.** Fetch fresh on every execute call.
5. **Never stage** `config.toml`, `*.env`, `*.key`, `secrets.*`, `config.local.*`, `cookies.txt`.
6. **Never use `print()`** in source. Use `utils/output.py` or the logger.
7. **Never hardcode** environment URLs, usernames, or passwords in tests.
8. **Safe mode on by default.** `commit=True` is blocked unless the environment has `safe_mode=False`.

`.claude/hooks/pre_tool_call.py` enforces rules 1 and 5 at tool-call time.

---

## File Map

```
src/hac_cli/
  cli/         cmd_env.py  cmd_groovy.py  cmd_scripts.py  app.py
  application/ execute_groovy.py  manage_environments.py
  domain/      models.py  ports.py  exceptions.py (7 typed exceptions)
  infrastructure/ hac_client.py  config_store.py  script_repository.py
  tui/         app.py  widgets.py
  utils/       logging.py  output.py
scripts/       cache/  catalog/  customer/  orders/  _templates/
tests/         unit/ (67 tests)  integration/ (opt-in)  conftest.py
docs/          architecture.md  getting-started.md  security.md  script-authoring.md
```

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `HAC_CONFIG_PATH` | project root | Override config directory |
| `HAC_SCRIPTS_PATH` | `<repo>/scripts` | Override script library root |
| `HAC_LOG_LEVEL` | `WARNING` | DEBUG / INFO / WARNING |
| `HAC_TEST_URL` | (unset) | Activates integration tests |

---

## Further Reading

Detailed rules live in `.claude/rules/` — read the relevant file before working in that area:

- `.claude/rules/hac-api.md` — HAC endpoints, auth flow, response formats
- `.claude/rules/workflows.md` — how to add scripts, commands, config fields, TUI widgets
- `.claude/rules/testing-patterns.md` — pytest-httpx mocking, CLI runner, AsyncMock
- `.claude/rules/coding-standards.md` — Python, Groovy, test conventions; what NOT to do
- `.claude/rules/common-prompts.md` — ready-made prompts for common extension tasks
