# hac-cli

> Execute SAP Commerce (Hybris) HAC Groovy scripts from your terminal — no browser needed.

[![CI](https://github.com/your-org/hac-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/hac-cli/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hac-cli.svg)](https://pypi.org/project/hac-cli/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/your-org/hac-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/hac-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- **Multi-environment** — store configs for dev, staging, prod; switch with `--env`
- **Secure credentials** — passwords in OS keychain (macOS Keychain / Windows Credential Manager), never on disk or in logs
- **Script library** — parameterized, categorized Groovy snippets with fuzzy search
- **Natural language** — `hac groovy run --env dev "clear all caches"` finds the right script
- **Rich output** — colored results, execution timing, stack traces
- **Interactive TUI** — `hac` with no args launches a full terminal UI (keyboard-driven)
- **Secret redaction** — all output passes through a redaction filter before display
- **Audit log** — every tool call logged to `~/.hac-cli/audit/`

## Installation

```bash
# Recommended: pipx (isolated install)
pipx install hac-cli

# Or: uv
uv tool install hac-cli
```

## Quick Start

```bash
# 1. Add an environment (password stored securely in OS keychain)
hac env add --name dev --url https://dev-hac.example.com --user admin

# 2. Test connectivity
hac env test dev

# 3. Execute a script from the library
hac groovy run --env dev --script cache/clear_all_caches

# 4. Execute a local file
hac groovy run --env dev --file my_script.groovy

# 5. Inline execution
hac groovy run --env dev --inline 'println flexibleSearchService.search("SELECT {pk} FROM {Product}", [:]).count'

# 6. Natural language script selection
hac groovy run --env dev "clear all caches"

# 7. Browse script library
hac scripts list
hac scripts search "order status"
hac scripts show orders/get_order_status

# 8. Interactive TUI
hac
```

## Interactive TUI

Launch `hac` with no arguments for the keyboard-driven TUI:

| Key        | Action                          |
|------------|---------------------------------|
| `Tab`      | Cycle between panels            |
| `Ctrl+R`   | Run selected script             |
| `Ctrl+T`   | Toggle commit / dry-run mode    |
| `/`        | Focus script search             |
| `Escape`   | Clear search                    |
| `Ctrl+N`   | Switch to next environment      |
| `q`        | Quit                            |

## Script Library

Scripts live in `scripts/` and use a frontmatter comment block:

```groovy
// @meta
// name: Clear All Caches
// description: Clears all SAP Commerce cache regions
// category: cache
// tags: [cache, performance, maintenance]
// @end

import de.hybris.platform.core.Registry
// ...
```

See [docs/script-authoring.md](docs/script-authoring.md) for full authoring guide.

## Configuration

Non-secret configuration is stored at `~/.hac-cli/config.toml`:

```toml
[environments.dev]
url      = "https://dev-hac.example.com"
username = "admin"
timeout  = 30
verify_ssl = true
```

Passwords are stored in the OS keychain — never in this file.

## Security

- Credentials stored in OS keychain (macOS Keychain / Windows Credential Manager / libsecret)
- All log output passes through a secret-redaction filter before display
- SSL verification enabled by default; only `--no-ssl-verify` overrides it (dev only)
- CSRF tokens fetched fresh on every execution — never cached
- Pre-commit hooks scan for secrets before every commit
- `detect-secrets` baseline enforced in CI

See [SECURITY.md](SECURITY.md) for the full security model and vulnerability reporting.

## Architecture

Clean architecture with ports/adapters pattern:

```
CLI (Typer) → Application (use-cases) → Domain (models, ports)
                                              ↑
                              Infrastructure (HAC HTTP client, keyring, config)
```

See [docs/architecture.md](docs/architecture.md) for the full diagram and HAC auth flow.

## Development

```bash
git clone https://github.com/your-org/hac-cli
cd hac-cli
make install   # installs deps + pre-commit hooks
make check     # lint + type-check + tests
make build     # produces dist/ wheel and sdist
```

Common commands:

| Command                  | Description                              |
|--------------------------|------------------------------------------|
| `make test`              | Unit tests with coverage                 |
| `make test-fast`         | Unit tests without coverage              |
| `make test-integration`  | Integration tests (requires HAC_TEST_URL)|
| `make lint`              | ruff linter                              |
| `make fmt`               | Auto-fix formatting                      |
| `make type-check`        | mypy strict mode                         |
| `make build`             | Build wheel + sdist                      |
| `make release-patch`     | Bump patch version and tag               |

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution guide.

## License

MIT
