# Coding Standards

## Python

- Python 3.11+ syntax: `match`, `tomllib`, `X | Y` unions, `datetime.now(timezone.utc)`
- `from __future__ import annotations` in every source file
- Type hints on all public functions; `mypy --strict` must pass
- `ruff` for linting and formatting — no separate black/isort/flake8
- Frozen dataclasses for value objects; unfrozen for mutable results (`ExecutionResult`)
- No comments on obvious code — only non-obvious WHY
- No `# type: ignore` without an explanatory comment

## Groovy scripts

- `binding.hasVariable("param")` guard on every parameter
- Beans via `Registry.getApplicationContext().getBean(Type.class)` (type-safe)
- Always `println` a meaningful result — HAC returns stdout as output
- Null-safe navigation: `order?.user?.uid ?: "(unknown)"`

## Tests

- `tests/unit/` — fast, no external I/O; all HTTP mocked via `pytest-httpx`
- `tests/integration/` — opt-in, gate with `HAC_TEST_URL` env var
- No hardcoded URLs or credentials anywhere in test files
- Fixtures in `conftest.py`

## What NOT to do

| Don't | Do instead |
|---|---|
| Run scripts with `--commit` | Keep `safe_mode=True` (default); use `--no-safe-mode` only when necessary |
| `print()` in source | `utils/output.print_*()` or logger |
| Import infrastructure in domain | Use ports (abstract base classes) |
| Import infrastructure directly in CLI/TUI | Go through application layer |
| Hardcode env URLs/passwords in tests | Use `conftest.py` fixtures + env vars |
| Add `# type: ignore` silently | Comment explaining the unavoidable reason |
| Bypass SSL in non-dev envs | Keep `verify_ssl=True`; fix the cert instead |
| Cache CSRF tokens | Fetch fresh on every execute call |
| `uv run pip install` | Add to `pyproject.toml` and run `uv sync` |
| Commit `config.toml` | It is gitignored — keep it that way |
