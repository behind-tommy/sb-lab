#!/bin/bash
# PreToolUse (matcher: Edit|Write). Blocks writing to .env files (secrets). .env.example is allowed.
input=$(cat)
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""')
base=$(basename "$path")
if [[ "$base" == .env || "$base" == .env.* ]] && [[ "$base" != .env.example && "$base" != .env.sample ]]; then
  echo "Blocked by harness: $base holds secrets and is edited by a human only. Put placeholders in .env.example instead." >&2
  exit 2
fi
exit 0
