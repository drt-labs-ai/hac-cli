.PHONY: install test test-fast test-integration lint fmt type-check check \
        build clean release-patch release-minor release-major

# ── Setup ────────────────────────────────────────────────────────────────────

install:
	uv sync --extra dev
	uv run pre-commit install
	@echo "✓ Development environment ready. Run 'make test' to verify."

# ── Testing ──────────────────────────────────────────────────────────────────

test:
	uv run pytest tests/unit/ -v

test-fast:
	uv run pytest tests/unit/ --no-cov -q

test-integration:
	@if [ -z "$$HAC_TEST_URL" ]; then \
	  echo "HAC_TEST_URL is not set. Export it before running integration tests."; \
	  echo "  export HAC_TEST_URL=https://dev-hac.example.com"; \
	  echo "  export HAC_TEST_PASSWORD=yourpassword"; \
	  exit 1; \
	fi
	uv run pytest tests/integration/ -v

test-all: test test-integration

# ── Code Quality ─────────────────────────────────────────────────────────────

lint:
	uv run ruff check src/ tests/

fmt:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

type-check:
	uv run mypy src/

check: lint type-check test
	@echo "✓ All checks passed."

# ── Build & Distribution ─────────────────────────────────────────────────────

build:
	uv build
	@echo "✓ Artifacts in dist/"
	@ls -lh dist/

clean:
	rm -rf dist/ build/ *.egg-info
	rm -rf .coverage htmlcov/ coverage.xml
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Clean."

# ── Release ──────────────────────────────────────────────────────────────────

release-patch: check
	uv run python scripts/bump_version.py patch

release-minor: check
	uv run python scripts/bump_version.py minor

release-major: check
	uv run python scripts/bump_version.py major

# ── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo "hac-cli development commands:"
	@echo ""
	@echo "  make install          Install dev dependencies + pre-commit hooks"
	@echo "  make test             Run unit tests with coverage"
	@echo "  make test-fast        Run unit tests without coverage (faster)"
	@echo "  make test-integration Run integration tests (requires HAC_TEST_URL)"
	@echo "  make lint             Run ruff linter"
	@echo "  make fmt              Auto-fix formatting issues"
	@echo "  make type-check       Run mypy"
	@echo "  make check            lint + type-check + test"
	@echo "  make build            Build wheel + sdist"
	@echo "  make clean            Remove build artifacts"
	@echo "  make release-patch    Bump patch version, tag, and push"
	@echo "  make release-minor    Bump minor version, tag, and push"
	@echo "  make release-major    Bump major version, tag, and push"
