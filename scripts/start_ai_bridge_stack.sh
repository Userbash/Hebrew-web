#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRIDGE_CMD="$PROJECT_ROOT/ai_bridge/scripts/bridge/exec.sh"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.ai.yml"

if [ ! -x "$BRIDGE_CMD" ]; then
  echo "[ERROR] BridgeOS exec script not found or not executable: $BRIDGE_CMD"
  exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "[ERROR] Compose file not found: $COMPOSE_FILE"
  exit 1
fi

echo "Starting AI Bridge stack from $COMPOSE_FILE..."
"$BRIDGE_CMD" podman compose -f "$COMPOSE_FILE" up -d --build

echo "AI Bridge stack is starting."
echo "Orchestrator: http://localhost:${ORCHESTRATOR_PORT:-8000}"
echo "Ollama: http://localhost:${AI_BRIDGE_LOCAL_LLM_PORT:-11434}"
