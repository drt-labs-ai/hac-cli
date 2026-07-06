# Getting Started

## Prerequisites

- Python 3.11+
- `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Access to a SAP Commerce HAC instance

## Installation

```bash
# Install globally with pipx (recommended)
pipx install hac-cli

# Or with uv
uv tool install hac-cli

# Or editable dev install
git clone https://github.com/your-org/hac-cli
cd hac-cli
uv sync --extra dev
```

## First-Time Setup

### 1. Add an environment

```bash
hac env add \
  --name dev \
  --url https://dev-hac.example.com \
  --user admin
# Prompts for password — stored securely in OS keychain
```

### 2. Test connectivity

```bash
hac env test dev
# Connection to 'dev' successful.
```

### 3. Run your first script

```bash
# From the built-in script library
hac groovy run --env dev --script cache/clear_all_caches

# From a local file
hac groovy run --env dev --file my_script.groovy

# Inline
hac groovy run --env dev --inline 'println "Hello from HAC!"'
```

## Configuration Reference

Non-secret configuration lives at `~/.hac-cli/config.toml`:

```toml
[environments.dev]
url        = "https://dev-hac.example.com"
username   = "admin"
timeout    = 30          # seconds
verify_ssl = true

[environments.staging]
url        = "https://staging-hac.example.com"
username   = "admin"
timeout    = 60
verify_ssl = true
```

Passwords are **never** stored here — they go to the OS keychain automatically.

## Common Workflows

### Check order status

```bash
hac groovy run --env dev --script orders/get_order_status
# When prompted for orderCode: 00000042
```

Or pass parameters inline:

```bash
hac groovy run --env dev --inline '
def orderCode = "00000042"
import de.hybris.platform.servicelayer.search.FlexibleSearchService
import de.hybris.platform.core.Registry
def fss = Registry.getApplicationContext().getBean(FlexibleSearchService.class)
def r = fss.search("SELECT {pk} FROM {Order} WHERE {code}=?c", [c: orderCode])
println r.result ? "Found: ${r.result[0].status}" : "Not found"
'
```

### Clear caches before a deployment

```bash
hac groovy run --env staging --script cache/clear_all_caches
```

### Find a customer

```bash
hac groovy run --env prod --script customer/find_customer
```

### Search scripts by keyword

```bash
hac scripts search "catalog sync"
hac scripts show catalog/sync_catalog
```

### Natural language execution

```bash
hac groovy exec --env dev "clear all caches"
hac groovy exec --env dev "find order 00000042"
```

## Interactive TUI

Run `hac` with no arguments to launch the full terminal UI:

```
┌─────────────────────────────────────────────┐
│ hac-cli           Environment: [dev ▼]       │
│ Mode: DRY RUN                                │
├──────────────────────────┬──────────────────┤
│ Search… [        ] [All▼]│  Preview         │
│ cache/clear_all_caches   │  // name: Clear  │
│ cache/clear_region       │  // category:... │
│ catalog/sync_catalog     │                  │
│ orders/get_order_status  ├──────────────────┤
│                          │  Output          │
│                          │  > SUCCESS 42ms  │
└──────────────────────────┴──────────────────┘
│ q Quit  F5 Run  Ctrl+T Commit  / Search      │
```

**Keyboard shortcuts:**
| Key | Action |
|---|---|
| `↑↓` | Navigate scripts |
| `F5` / `Enter` | Execute selected script |
| `/` | Focus search input |
| `Esc` | Clear search |
| `e` | Cycle to next environment |
| `Ctrl+T` | Toggle commit/dry-run mode |
| `q` | Quit |

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `HAC_CONFIG_PATH` | `~/.hac-cli` | Override config directory |
| `HAC_SCRIPTS_PATH` | `<install>/scripts` | Override script library root |
| `HAC_LOG_LEVEL` | `WARNING` | Log level: DEBUG, INFO, WARNING |
| `HAC_TEST_URL` | (unset) | Enable integration tests |

## Troubleshooting

### Authentication fails

1. Test with curl: `curl -v https://your-hac/login` — confirm the URL is reachable
2. Check SSL: add `--no-ssl-verify` if using self-signed certs on dev
3. Re-enter credentials: `hac env add --name dev --url ... --user admin` (overwrites existing)

### CSRF token not found

HAC version mismatch. The tool looks for `<meta name="_csrf" content="...">` in the
scripting page HTML. If your HAC version uses a different CSRF mechanism, open an issue.

### Script output is empty

HAC returns `println` output as `executionResult` or `outputText` in the JSON response.
Check that your script actually prints something. Use `return "value"` as a fallback.

### SSL certificate errors

```bash
hac env add --name dev --url ... --no-ssl-verify
```

Never use `--no-ssl-verify` in production environments.
