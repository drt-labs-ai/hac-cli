# Security Model

## Credential Storage

Passwords are stored in **`config.toml`** at the project root alongside other environment
configuration. This is intentional for a local developer productivity tool:

```toml
[environments.dev]
url      = "https://dev-hac.example.com"
username = "admin"
password = "yourpassword"
timeout  = 30
verify_ssl = true
```

`config.toml` is listed in `.gitignore` and must never be committed. The pre-commit
hook will block any attempt to stage it.

## Secret Scanning

Every commit is scanned by **detect-secrets** (via pre-commit). The `.secrets.baseline`
file tracks known false positives. CI also runs the scan on every push.

Patterns detected include:
- Passwords (`password = "..."`)
- API keys (`api_key = "..."`)
- Private keys (PEM headers)
- Bearer tokens
- AWS/GCP/Azure credentials

## Log Redaction

All log output passes through `utils/logging.RedactingFilter` before being written.
The filter scrubs patterns matching:
- `password=`, `token=`, `Authorization:`, `Cookie:`, `j_password=`, `CSRF`

This applies to all loggers obtained via `utils/logging.get_logger()`.

## Transport Security

- SSL verification is **enabled by default** for all environments
- `--no-ssl-verify` is available only for development environments; it is visible
  in `hac env list` output as a red warning
- HTTP/2 is used automatically when the server supports it (via httpx)

## Safe Mode

All environments have `safe_mode = true` by default. When safe mode is enabled, any execution
with `commit=True` is blocked at the application layer (`ExecuteGroovyService.execute()`) before
any HTTP request is made. This prevents accidental data modifications regardless of how the tool
is invoked (CLI, TUI, or application layer directly).

```toml
# config.toml
[environments.dev]
safe_mode = true   # default — commit=True blocked
```

To allow commits on a specific environment (e.g. a dedicated write-capable env):

```bash
hac env add --name dev-write --url ... --user admin --password ... --no-safe-mode
```

`hac env list` shows `on` (green) or `off` (yellow) in the Safe Mode column.

---

## CSRF Protection

CSRF tokens are:
- Fetched fresh before every script execution (never cached across calls)
- Sent in the `X-CSRF-TOKEN` header (HAC's expected format)
- Never logged (covered by `RedactingFilter`)

## Pre-commit Hooks

`.pre-commit-config.yaml` runs:

1. **detect-secrets** — scans all staged files against the baseline
2. **ruff** — linting (catches insecure patterns via `B` rules)
3. **no-commit-to-branch** — blocks direct commits to `main`/`master`
4. **detect-private-key** — blocks PEM files

## Claude Code Hooks

`.claude/hooks/pre_tool_call.py` blocks or warns on:

| Trigger | Action |
|---|---|
| `git push --force` (without `--force-with-lease`) | BLOCK |
| `git add <file-with-secret-name>` | BLOCK |
| `rm -rf /` (system paths) | BLOCK |
| Hardcoded secret patterns in Write/Edit content | WARN |

`.claude/hooks/post_tool_call.py` writes a JSON audit log to
`~/.hac-cli/audit/<date>.log` for every tool call.

## Git Protection

`.gitignore` blocks:
```
*.key  *.pem  *.p12  *.pfx
secrets.toml  secrets.yaml  secrets.json
*credentials*  *password*
cookies.txt  *.cookie
.env  .env.*  config.local.*
.hac_sessions/  .hac_tokens/
.claude/settings.local.json
```

## Reporting Security Issues

Do not open public GitHub issues for security vulnerabilities.
Email: security@your-org.com
