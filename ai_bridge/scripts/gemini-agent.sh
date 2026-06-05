#!/usr/bin/env bash
set -euo pipefail

TASK_FILE="${1:?Usage: scripts/gemini-agent.sh task-file}"

resolve_gemini_cli() {
  if [[ -n "${GEMINI_CLI_BIN:-}" ]]; then
    if command -v "${GEMINI_CLI_BIN}" >/dev/null 2>&1; then
      printf '%s\n' "${GEMINI_CLI_BIN}"
      return 0
    fi
  fi

  for candidate in gemini google-gemini gemini-cli; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  if command -v npx >/dev/null 2>&1; then
    printf '%s\n' "npx @google/gemini-cli"
    return 0
  fi

  return 1
}

CLI_SPEC="$(resolve_gemini_cli)"

NODE_DIR=""
if [[ -z "$(command -v node 2>/dev/null)" ]] && [[ -n "$(command -v npx 2>/dev/null)" ]]; then
  NODE_DIR="$(dirname "$(command -v npx)")"
  export PATH="${NODE_DIR}:${PATH}"
fi

if command -v flatpak-spawn >/dev/null 2>&1; then
  if [[ "${CLI_SPEC}" == "npx @google/gemini-cli" ]]; then
    exec flatpak-spawn --host npx @google/gemini-cli < "$TASK_FILE"
  fi
  exec flatpak-spawn --host "${CLI_SPEC}" < "$TASK_FILE"
fi

if [[ "${CLI_SPEC}" == "npx @google/gemini-cli" ]]; then
  exec npx @google/gemini-cli < "$TASK_FILE"
fi

exec "${CLI_SPEC}" < "$TASK_FILE"
