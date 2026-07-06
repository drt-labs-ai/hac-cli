# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

We provide security fixes for the latest stable release. After a fix is available, we strongly recommend upgrading immediately.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

To report a security vulnerability, email the maintainers directly at the address listed in `pyproject.toml`. Include:

1. A description of the vulnerability and its potential impact
2. Steps to reproduce or a proof-of-concept (not a working exploit)
3. Affected versions
4. Any suggested mitigations

You will receive an acknowledgement within 48 hours. We aim to release a patch within 14 days for critical issues.

## Security Model

hac-cli is a developer tool that runs locally and communicates with SAP Commerce HAC over HTTPS.

### Credential Storage

- Passwords are stored exclusively in the OS keychain (macOS Keychain, Windows Credential Manager, or libsecret on Linux)
- No credentials are written to disk, logged, or included in the config file at `~/.hac-cli/config.toml`
- The `EnvSecretStore` adapter (used only for CI integration tests) reads passwords from environment variables — it must never be used in production

### Network Security

- SSL verification is enabled by default (`verify_ssl = true`)
- The `--no-ssl-verify` flag exists for development environments with self-signed certificates; it must never be used against production
- CSRF tokens are fetched fresh on every script execution — they are never cached

### Secret Redaction

- All terminal output passes through `utils/logging.redact()` before emission
- Pre-commit hooks scan staged files for secrets using `detect-secrets`
- The `.secrets.baseline` in the repository is the allowed-baseline for detect-secrets; any newly detected secret will fail CI

### What hac-cli Does NOT Do

- Store sessions or cookies between CLI invocations (sessions are in-memory only)
- Cache passwords or tokens on disk
- Send telemetry or usage data anywhere

## Audit Logging

Claude Code hook activity is logged to `~/.hac-cli/audit/<date>.log`. This log records tool names and file paths but never passwords or token values.

## Dependency Security

Dependencies are pinned in `uv.lock`. To check for known vulnerabilities:

```bash
uv run pip-audit
```

We review dependency advisories on a monthly basis and patch critical CVEs within 7 days.
