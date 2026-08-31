#!/bin/bash
# PreToolUse (matcher: Bash). Blocks destructive shell and SQL commands.
input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
if printf '%s' "$cmd" | grep -qiE 'rm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\s|rm\s+-rf\s+[/~]|git\s+reset\s+--hard|git\s+clean\s+-fd|DROP\s+(TABLE|DATABASE|SCHEMA)|TRUNCATE\s|DELETE\s+FROM\s+\w+\s*;'; then
  echo "Blocked by harness: destructive command. If this is intentional, a human runs it by hand after a backup." >&2
  exit 2
fi
exit 0
