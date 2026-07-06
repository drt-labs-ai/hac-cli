#!/usr/bin/env bash
# Delegates to pre_tool_call.py (same directory).
# Keeping a .sh wrapper lets Claude Code discover the hook via the settings.json
# command string while the actual logic lives in maintainable Python.
exec python3 "$(dirname "$0")/pre_tool_call.py"
