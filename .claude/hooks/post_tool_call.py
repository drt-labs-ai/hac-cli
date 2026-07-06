#!/usr/bin/env python3
"""Post-tool-call audit logger for hac-cli.

Appends a single-line JSON entry to ~/.hac-cli/audit/<date>.log
after every tool call. Never raises — audit failure must not block work.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    try:
        data: dict = json.load(sys.stdin)
        tool_name: str = data.get("tool_name", "unknown")

        log_dir = Path.home() / ".hac-cli" / "audit"
        log_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = log_dir / f"{today}.log"

        entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tool": tool_name,
        }

        # Log the Bash command (redacted) or file path for Write/Edit
        if tool_name == "Bash":
            cmd = data.get("tool_input", {}).get("command", "")
            entry["cmd"] = cmd[:120]  # truncate long commands
        elif tool_name in ("Write", "Edit"):
            entry["path"] = data.get("tool_input", {}).get("file_path", "")

        with log_file.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    except Exception:
        pass  # audit failures are silent

    sys.exit(0)


if __name__ == "__main__":
    main()
