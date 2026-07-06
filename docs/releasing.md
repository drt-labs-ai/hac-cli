# Release Process

hac-cli uses semantic versioning (`MAJOR.MINOR.PATCH`) and a fully automated release pipeline via GitHub Actions.

## Prerequisites

- You are on the `main` branch with a clean working tree
- All CI checks are green
- `CHANGELOG.md` has entries under `## [Unreleased]` describing what changed

## Steps

### 1. Run the Release Command

```bash
# For a bug fix release
make release-patch   # 0.1.0 → 0.1.1

# For a new feature release (backwards-compatible)
make release-minor   # 0.1.0 → 0.2.0

# For a breaking change
make release-major   # 0.1.0 → 1.0.0
```

`make release-<part>` runs `make check` first (lint + type-check + tests), then calls `scripts/bump_version.py` which:
1. Validates the working tree is clean
2. Bumps the version in `pyproject.toml`
3. Moves `## [Unreleased]` to `## [X.Y.Z] — YYYY-MM-DD` in `CHANGELOG.md`
4. Commits both files with message `chore: release vX.Y.Z`
5. Creates an annotated git tag `vX.Y.Z`

### 2. Push

```bash
git push && git push --tags
```

### 3. GitHub Actions Takes Over

Pushing a `v*.*.*` tag triggers the release workflow:

1. **validate** — re-runs lint + tests + verifies tag matches `pyproject.toml`
2. **build** — `uv build` → `twine check` → uploads artifacts
3. **publish** — publishes to PyPI via OIDC (no API token needed)
4. **github-release** — creates a GitHub Release with the CHANGELOG section as release notes and the wheel + sdist attached

## Updating CHANGELOG Before Release

The `## [Unreleased]` section should be kept up to date as features land. Before releasing, review and clean it up:

```markdown
## [Unreleased]

### Added
- Brief description of new feature

### Fixed
- Brief description of bug fix

### Changed
- Brief description of behaviour change

### Removed
- Brief description of removed feature
```

Use `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security` as section headers (Keep a Changelog convention).

## Hotfix Process

For critical security or bug fixes on a released version:

1. Create a branch from the tag: `git checkout -b hotfix/0.1.1 v0.1.0`
2. Apply the fix
3. Run `make check` to verify
4. Run `scripts/bump_version.py patch` manually (not via `make release-patch`, which requires main)
5. Push the branch and tag: `git push origin hotfix/0.1.1 --tags`
6. Open a PR to merge the fix back to `main`

## Environment: PyPI

The `publish` job requires a GitHub environment named `pypi` with OIDC trusted publishing configured on PyPI. To set this up:

1. Go to PyPI → Your project → Publishing → Add a new publisher
2. Set: Owner = your-org, Repository = hac-cli, Workflow = release.yml, Environment = pypi
3. Create the `pypi` environment in GitHub repo settings (no secrets needed — OIDC handles auth)
