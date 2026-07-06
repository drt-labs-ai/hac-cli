# Changelog

All notable changes to hac-cli are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-07-06

### Added

**Phase 2 — Repository Bootstrap**
- Project skeleton with clean architecture (domain / application / infrastructure / CLI / TUI)
- Domain models: `Environment`, `ExecutionContext`, `ExecutionResult`, `ScriptMeta`
- Port interfaces: `IHacClient`, `ISecretStore`, `IConfigStore`, `IScriptRepository`
- Domain exceptions: `HacAuthenticationError`, `HacConnectionError`, `ScriptExecutionError`, and more
- TOML config store at `~/.hac-cli/config.toml`
- OS keychain secret store (`KeyringSecretStore`) via `keyring`
- Filesystem-backed Groovy script library with `// @meta` frontmatter and fuzzy search (`thefuzz`)
- CLI commands: `hac env`, `hac groovy`, `hac scripts`
- Structured logging with secret-redaction filter
- GitHub Actions CI (lint + test matrix on 3 OS × 2 Python + secrets scan)
- GitHub Actions release pipeline (build → PyPI publish → GitHub Release)
- Pre-commit hooks: detect-secrets, ruff, mypy

**Phase 3 — HAC HTTP Client**
- Full Spring Security form-login flow with CSRF token extraction
- Session caching (in-memory, 30-minute TTL) with automatic re-authentication
- CSRF token fetched fresh on every `execute()` call
- `_parse_execution_response()` handles both `outputText`/`executionResult` response formats
- `BeautifulSoup` parser handles `<meta name="_csrf">` and `<input name="_csrf">` variants
- 34 unit tests with `pytest-httpx` covering auth, re-auth, timeouts, CSRF, and response parsing

**Phase 4 — TUI and Application Layer**
- Textual TUI (`HacApp`) with reactive env selector, commit/dry-run toggle, script browser
- Script search and category filter in TUI
- `@work(exclusive=True, thread=False)` for non-blocking async execution
- Application use-cases: `ExecuteGroovyUseCase`, `ListScriptsUseCase`, `SearchScriptsUseCase`
- `HAC_CONFIG_PATH` and `HAC_SCRIPTS_PATH` env vars for test isolation (lazy resolution)
- 8 CLI tests via `CliRunner` with env-var injection
- 11 application-layer tests covering inline/file/library/error paths

**Phase 5 — Claude Configuration**
- `CLAUDE.md` with architecture overview, HAC API reference, testing patterns, and 6 Claude prompts
- `.claude/settings.json` — pre/post tool call hooks, MCP servers (filesystem + sequential-thinking)
- `pre_tool_call.py` — blocks dangerous git commands, secret-file staging, and hardcoded secrets in writes
- `post_tool_call.py` — JSON audit log to `~/.hac-cli/audit/<date>.log`
- `docs/architecture.md` — layer diagrams and HAC auth flow
- `docs/getting-started.md` — installation, config, TUI keyboard shortcuts, troubleshooting
- `docs/security.md` — credential storage, audit logging, pre-commit hooks
- `docs/script-authoring.md` — frontmatter format, Spring beans, FlexibleSearch patterns

**Phase 6 — Testing, Documentation, Packaging**
- `EnvSecretStore` — env-var-backed secret store for CI integration tests
- Integration test suite (`tests/integration/`) with session fixtures and auto-skip when HAC unavailable
- 6 integration smoke tests: connectivity, Groovy execution, error capture, session reuse, dry-run
- `Makefile` with `install`, `test`, `test-fast`, `test-integration`, `lint`, `fmt`, `type-check`, `check`, `build`, `clean`, `release-*`
- `scripts/bump_version.py` — version bump utility (patch/minor/major), CHANGELOG update, git tag
- CI: added `build` job (package verification via twine) and opt-in `integration` job
- Release: added `validate` job (lint + test + version tag check before publish), CHANGELOG extraction for GitHub Release notes
- `CONTRIBUTING.md` — dev setup, conventions, PR process, adding scripts
- `SECURITY.md` — security model, responsible disclosure, dependency audit
- Updated `README.md` — PyPI + coverage badges, TUI keyboard reference, architecture summary, make command table
