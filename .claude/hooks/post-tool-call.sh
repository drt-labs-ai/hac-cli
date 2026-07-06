#!/usr/bin/env bash
# Delegates to post_tool_call.py (same directory).
exec python3 "$(dirname "$0")/post_tool_call.py"
