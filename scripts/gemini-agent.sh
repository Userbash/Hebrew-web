#!/usr/bin/env bash
set -euo pipefail

TASK_FILE="${1:?Usage: scripts/gemini-agent.sh task-file}"

if command -v flatpak-spawn >/dev/null 2>&1; then
  HOST="flatpak-spawn --host"
else
  HOST=""
fi

$HOST npx @google/gemini-cli < "$TASK_FILE"
