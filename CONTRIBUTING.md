# Contributing to hac-cli

Thank you for your interest in contributing. This guide covers the development workflow, conventions, and PR process.

## Development Setup

```bash
git clone https://github.com/your-org/hac-cli
cd hac-cli

# Install dependencies + pre-commit hooks
make install

# Verify everything works
make check
```

Requirements: Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Running Tests

```bash
# Unit tests (fast, no external dependencies)
make test

# Unit tests without coverage (fastest feedback loop)
make test-fast

# Integration tests against a real HAC instance
export HAC_TEST_URL=https://dev-hac.example.com
export HAC_TEST_PASSWORD=yourpassword
make test-integration
```

Unit tests must pass before any PR can merge. Integration tests are optional for contributors who don't have access to a HAC instance.

## Code Style

This project uses **ruff** for linting and formatting (replaces black + isort + flake8):

```bash
make fmt        # auto-fix formatting issues
make lint       # check without auto-fixing
make type-check # mypy strict mode
```

Rules enforced: `E, W, F, I, N, UP, B, A, C4, SIM, RUF` — see `pyproject.toml` for the full list.

Key conventions:
- No `print()` calls in source — use `utils/output.py` or the logger
- All log messages pass through `utils/logging.redact()` before emission
- No hardcoded URLs, usernames, or passwords anywhere — not even in tests
- No secrets on disk — `KeyringSecretStore` only

## Project Structure

```
src/hac_cli/
  domain/          # Pure domain models, ports (interfaces), exceptions — no I/O
  application/     # Use-cases that orchestrate domain + infrastructure
  infrastructure/  # Concrete implementations (HAC HTTP client, config, keyring)
  cli/             # Typer command definitions
  tui/             # Textual TUI app
  utils/           # Shared helpers (logging, output)

tests/
  unit/            # Fast tests with mocked I/O (pytest-httpx)
  integration/     # Tests against a real HAC instance (opt-in)

scripts/           # Developer utilities (version bumping)
docs/              # Architecture, getting started, security, script authoring
```

## Adding a Groovy Script to the Library

1. Create a `.groovy` file under `scripts/<category>/`
2. Add the frontmatter block at the top:

```groovy
// @meta
// name: My Script Name
// description: One-sentence description of what this script does
// category: cache
// tags: [cache, performance]
// @end
```

3. Write the script — see `docs/script-authoring.md` for patterns and best practices
4. Add it to the category's section in the library tests if relevant

## Adding a New Infrastructure Adapter

1. Define the interface in `domain/ports.py` (if it doesn't exist)
2. Implement it in `infrastructure/`
3. Wire it up in the application layer
4. Add unit tests that mock the I/O boundary (`tests/unit/`)

## Pull Request Process

1. **Fork** the repository and create a branch from `main`
2. **Write tests** — unit coverage must not drop below 80%
3. **Run `make check`** — lint + type-check + tests must all pass
4. **Describe the change** — PR title should be concise (under 70 chars); use the body for details
5. **One concern per PR** — don't bundle unrelated changes

PR titles follow conventional commits:
- `feat: add batch execution support`
- `fix: handle CSRF token missing from login page`
- `chore: bump httpx to 0.28`
- `docs: add FlexibleSearch examples to script library`

## Security Issues

Do **not** open a public issue for security vulnerabilities. See [SECURITY.md](SECURITY.md) for the responsible disclosure process.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
