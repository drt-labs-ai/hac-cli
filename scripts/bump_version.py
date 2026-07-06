#!/usr/bin/env python3
"""Bump the version in pyproject.toml, update CHANGELOG.md, and create a git tag.

Usage:
  python scripts/bump_version.py patch    # 0.1.0 → 0.1.1
  python scripts/bump_version.py minor    # 0.1.0 → 0.2.0
  python scripts/bump_version.py major    # 0.1.0 → 1.0.0

The script:
  1. Reads the current version from pyproject.toml
  2. Bumps the requested part
  3. Writes the new version back to pyproject.toml
  4. Moves the [Unreleased] section in CHANGELOG.md to the new version
  5. Commits both files
  6. Creates an annotated git tag vX.Y.Z
  7. Prints next steps (push + push tags)
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parents[1]
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"


# ── Version helpers ──────────────────────────────────────────────────────────


def read_current_version() -> tuple[int, int, int]:
    content = PYPROJECT.read_text()
    m = re.search(r'^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content, re.MULTILINE)
    if not m:
        print("ERROR: Could not find version in pyproject.toml", file=sys.stderr)
        sys.exit(1)
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def bump(current: tuple[int, int, int], part: str) -> tuple[int, int, int]:
    major, minor, patch = current
    match part:
        case "major":
            return major + 1, 0, 0
        case "minor":
            return major, minor + 1, 0
        case "patch":
            return major, minor, patch + 1
        case _:
            print(f"ERROR: Unknown bump part '{part}'. Use: major | minor | patch", file=sys.stderr)
            sys.exit(1)


def write_version(new: tuple[int, int, int]) -> None:
    old = read_current_version()
    old_str = f'{old[0]}.{old[1]}.{old[2]}'
    new_str = f'{new[0]}.{new[1]}.{new[2]}'
    content = PYPROJECT.read_text()
    updated = content.replace(f'version = "{old_str}"', f'version = "{new_str}"', 1)
    if updated == content:
        print(f"ERROR: Could not replace version '{old_str}' in pyproject.toml", file=sys.stderr)
        sys.exit(1)
    PYPROJECT.write_text(updated)


# ── Changelog helpers ────────────────────────────────────────────────────────


def update_changelog(new_version: str) -> None:
    if not CHANGELOG.exists():
        return

    today = date.today().isoformat()
    content = CHANGELOG.read_text()

    if f"[{new_version}]" in content:
        print(f"WARNING: [{new_version}] already exists in CHANGELOG.md — skipping update")
        return

    updated = content.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n\n## [{new_version}] — {today}",
        1,
    )
    CHANGELOG.write_text(updated)


# ── Git helpers ──────────────────────────────────────────────────────────────


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=ROOT)
    return result.stdout.strip()


def git_tag(version: str) -> None:
    git("add", str(PYPROJECT), str(CHANGELOG))
    git("commit", "-m", f"chore: release v{version}\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>")
    git("tag", "-a", f"v{version}", "-m", f"Release v{version}")


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: bump_version.py <major|minor|patch>", file=sys.stderr)
        sys.exit(1)

    part = sys.argv[1].lower()
    current = read_current_version()
    new = bump(current, part)
    new_str = f"{new[0]}.{new[1]}.{new[2]}"
    old_str = f"{current[0]}.{current[1]}.{current[2]}"

    print(f"Bumping {part}: {old_str} → {new_str}")

    # Check for uncommitted changes
    status = git("status", "--porcelain")
    if status:
        print("ERROR: Working tree has uncommitted changes. Commit or stash first.", file=sys.stderr)
        sys.exit(1)

    write_version(new)
    update_changelog(new_str)
    git_tag(new_str)

    print(f"\n✓ Version bumped to {new_str}")
    print(f"✓ Tagged v{new_str}")
    print("\nNext steps:")
    print("  git push && git push --tags")
    print("  (GitHub Actions will publish to PyPI automatically)")


if __name__ == "__main__":
    main()
