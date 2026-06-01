#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

python3 ai_bridge/scripts/prepare_clean_env.py

if [ -f .env.gemini.local ]; then
  set -a
  . ./.env.gemini.local
  set +a
fi

export AI_BRIDGE_CODEX_ECONOMY_MODE=${AI_BRIDGE_CODEX_ECONOMY_MODE:-true}
export AI_BRIDGE_POLICY_MODE=${AI_BRIDGE_POLICY_MODE:-legacy}
export PYTHONPATH=.

exec .venv_ai_bridge/bin/python -m ai_bridge.scripts.orchestrator_daemon
