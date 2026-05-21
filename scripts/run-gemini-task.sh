#!/usr/bin/env bash
set -euo pipefail

TASK_ID="${1:?task id required}"
TASK_FILE=".agent/tasks/${TASK_ID}-gemini.txt"
REPORT_FILE=".agent/reports/${TASK_ID}-gemini.md"

mkdir -p .agent/reports

scripts/gemini-agent.sh "$TASK_FILE" > "$REPORT_FILE"

echo "[DONE] Gemini report saved to $REPORT_FILE"
