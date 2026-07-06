# hac-cli

> Execute SAP Commerce (Hybris) HAC Groovy scripts from your terminal — no browser needed.

[![CI](https://github.com/your-org/hac-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/hac-cli/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Multi-environment** — store configs for dev, staging, prod; switch with `--env`
- **Secure credentials** — passwords stored in OS keychain (macOS Keychain / Windows Credential Manager), never on disk
- **Script library** — parameterized, categorized Groovy snippets with fuzzy search
- **Natural language** — `hac groovy exec --env dev "clear all caches"` finds the right script
- **Rich output** — colored results, timing, stack traces
- **Interactive TUI** — `hac` with no args launches a full terminal UI

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
hac groovy exec --env dev "clear all caches"

# 7. Browse script library
hac scripts list
hac scripts search "order status"
hac scripts show orders/get_order_status

# 8. Interactive TUI
hac
```

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

## Development

```bash
# Clone and install in dev mode
git clone https://github.com/your-org/hac-cli
cd hac-cli
uv sync --extra dev
pre-commit install

# Run tests
uv run pytest tests/unit/

# Lint
uv run ruff check src/
uv run mypy src/
```

## Security

- Credentials stored in OS keychain (macOS Keychain / Windows Credential Manager / libsecret)
- All log output passes through a secret-redaction filter
- SSL verification enabled by default
- Pre-commit hooks scan for secrets before every commit
- `detect-secrets` baseline enforced in CI

## License

MIT
