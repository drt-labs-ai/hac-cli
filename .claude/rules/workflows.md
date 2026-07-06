# Development Workflows

## Add a Groovy script to the library

1. Create `scripts/<category>/<name>.groovy`
2. Add `// @meta … // @end` frontmatter (copy `scripts/_templates/script.groovy.template`)
3. Verify: `uv run hac scripts show <category>/<name>`
4. Dry-run: `uv run hac groovy run --env local --script <category>/<name>`

## Add a new CLI subcommand group

1. Create `src/hac_cli/cli/cmd_<name>.py` with `<name>_app = typer.Typer(...)`
2. Register in `cli/app.py` via `app.add_typer(<name>_app, name="<name>", help="...")`
3. Add use case in `application/<name>.py`
4. Add unit tests in `tests/unit/test_cli_<name>.py` using `CliRunner` + env var injection

## Add a new Environment config field

1. Add field to `domain/models.py` `Environment` dataclass (with default)
2. Serialize in `infrastructure/config_store.py` → `save_environment()`
3. Deserialize in `config_store.py` → `_dict_to_env()`
4. Add `--new-flag` option to `cli/cmd_env.py` `add_env()`
5. Thread through `application/manage_environments.py` `add_environment()`

## Add a TUI widget or screen

1. Add Textual widget to `tui/widgets.py` or a new `tui/<screen>.py`
2. Import and compose in `tui/app.py`
3. Add reactive property if the widget responds to app state
4. Wire keyboard binding in `BINDINGS` list

## Run tests

```bash
uv run pytest tests/unit/ -v                    # unit tests + coverage
uv run pytest tests/unit/ -v --no-cov           # fast, no coverage overhead
uv run pytest tests/unit/test_hac_client.py -v  # single file
HAC_TEST_URL=https://dev-hac.example.com uv run pytest tests/integration/
```

## Code quality

```bash
uv run ruff check src/ tests/    # lint
uv run ruff format src/ tests/   # format
uv run mypy src/                 # type check (strict)
```

## Release a new version

```bash
# 1. Bump version in pyproject.toml
# 2. Update CHANGELOG.md — move Unreleased → [X.Y.Z] with today's date
uv run pytest tests/unit/ && uv run ruff check src/
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release vX.Y.Z"
git tag vX.Y.Z && git push && git push --tags
# GitHub Actions release.yml handles PyPI publish + GitHub Release
```

## Debug an auth failure

```bash
HAC_LOG_LEVEL=DEBUG hac env test dev 2>&1 | head -50
# Check: URL reachable, redirect location has no "error", scripting page returns <meta name="_csrf">
```

To dump raw HTTP, add to `HacHttpClient._make_client()` temporarily:
```python
event_hooks={"request": [lambda r: print(r.url)],
             "response": [lambda r: print(r.status_code, r.url)]}
```
