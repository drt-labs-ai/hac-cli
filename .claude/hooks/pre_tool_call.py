#!/usr/bin/env python3
"""Pre-tool-call security hook for hac-cli.

Receives a JSON tool-call descriptor on stdin.
Exits 1 (blocks the call) or prints a warning to stderr and exits 0.

Schema received on stdin:
  { "tool_name": "Bash", "tool_input": { "command": "..." } }
  { "tool_name": "Write", "tool_input": { "file_path": "...", "content": "..." } }
  { "tool_name": "Edit",  "tool_input": { "file_path": "...", "new_string": "..." } }
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_SECRET_STAGE_PATTERNS = re.compile(
    r"git\s+add\b.+\b("
    r"password|passwd|token|secret|credential|api_key|apikey|\.env|cookie|\.pem|\.key"
    r")\b",
    re.IGNORECASE,
)

_FORCE_PUSH_PATTERN = re.compile(
    r"git\s+push\b.+--force(?!-with-lease)",
    re.IGNORECASE,
)

_DANGEROUS_RM_PATTERN = re.compile(
    r"rm\s+-[a-z]*r[a-z]*f[a-z]*\s+/(?!(tmp|var/folders|private/tmp))",
    re.IGNORECASE,
)

_HARDCODED_SECRET_PATTERNS = [
    re.compile(r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']', re.IGNORECASE),
    re.compile(r'(?:api_key|apikey|secret_key|client_secret)\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
    re.compile(r'(?:Authorization:\s+Bearer\s+)[A-Za-z0-9+/=._-]{20,}', re.IGNORECASE),
    re.compile(r'j_password\s*[=:]\s*["\'][^"\']{4,}["\']', re.IGNORECASE),
]

_SAFE_PATHS_FOR_SECRETS = (
    "/tests/fixtures/",
    "/docs/",
    ".md",
    ".secrets.baseline",
    "CHANGELOG",
)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    try:
        data: dict = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # malformed input — let Claude handle it

    tool_name: str = data.get("tool_name", "")
    tool_input: dict = data.get("tool_input", {})

    if tool_name == "Bash":
        _check_bash(tool_input.get("command", ""))

    elif tool_name in ("Write", "Edit"):
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content") or tool_input.get("new_string") or ""
        _check_write(file_path, content)

    sys.exit(0)


def _check_bash(command: str) -> None:
    if _FORCE_PUSH_PATTERN.search(command):
        _block(
            "Force push without --force-with-lease is not allowed.\n"
            "Use: git push --force-with-lease  (safer alternative)"
        )

    m = _SECRET_STAGE_PATTERNS.search(command)
    if m:
        _block(
            f"Attempt to stage a file matching a secret pattern: '{m.group(1)}'\n"
            "Passwords belong in config.toml (project root, gitignored) — never in a staged file."
        )

    if _DANGEROUS_RM_PATTERN.search(command):
        _block("Dangerous 'rm -rf /' style command is not allowed.")


def _check_write(file_path: str, content: str) -> None:
    if any(p in file_path for p in _SAFE_PATHS_FOR_SECRETS):
        return

    for pattern in _HARDCODED_SECRET_PATTERNS:
        if pattern.search(content):
            _warn(
                f"Possible hardcoded credential pattern in {Path(file_path).name}\n"
                "Store secrets in config.toml (project root, gitignored) — not in source files."
            )
            break  # one warning is enough


def _block(message: str) -> None:
    print(f"[hac-cli hook] BLOCKED: {message}", file=sys.stderr)
    sys.exit(1)


def _warn(message: str) -> None:
    print(f"[hac-cli hook] WARNING: {message}", file=sys.stderr)


if __name__ == "__main__":
    main()
