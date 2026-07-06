#!/usr/bin/env bash
# Blocks tool calls that might expose secrets.
# Receives the tool call as JSON on stdin.

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")
TOOL_INPUT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('tool_input','')))" 2>/dev/null || echo "{}")

# Block commits that touch secret-like files
if [[ "$TOOL_NAME" == "Bash" ]]; then
  COMMAND=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('command',''))" 2>/dev/null || echo "")

  SECRET_PATTERNS=("password" "token" "secret" "credentials" "api_key" "apikey" ".env" "cookie")
  for pattern in "${SECRET_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qi "git add.*$pattern"; then
      echo "BLOCKED: Attempt to stage a file matching secret pattern: $pattern" >&2
      exit 1
    fi
  done
fi

exit 0
