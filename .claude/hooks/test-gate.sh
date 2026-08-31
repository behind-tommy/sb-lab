#!/bin/bash
# PreToolUse (matcher: Bash). Before any `git commit`, run lint + types + tests. Red = no commit.
input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
if printf '%s' "$cmd" | grep -qE '^\s*git\s+commit|&&\s*git\s+commit|;\s*git\s+commit'; then
  cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
  out=$( (uv run ruff check . && uv run mypy . && uv run pytest -q) 2>&1 )
  status=$?
  if [ $status -ne 0 ]; then
    echo "Blocked by harness: checks failed before commit. Fix the code (never the tests) and try again." >&2
    echo "$out" | tail -n 40 >&2
    exit 2
  fi
fi
exit 0
