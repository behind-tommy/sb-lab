#!/bin/bash
# PreToolUse (matcher: Bash). Blocks `git push` to main/master and any force push.
# Exit 2 = block the action and send the message back to the agent.
input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
if printf '%s' "$cmd" | grep -qE 'git\s+push.*(\s|/)(main|master)(\s|$)|git\s+push\s+.*--force|git\s+push\s+-f\b'; then
  echo "Blocked by harness: pushes to main go through a pull request. Create a branch (git checkout -b feature/...) and push that." >&2
  exit 2
fi
exit 0
