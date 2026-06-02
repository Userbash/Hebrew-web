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
export AI_BRIDGE_OPENAI_AUTO_MODEL=${AI_BRIDGE_OPENAI_AUTO_MODEL:-true}
export OPENAI_SESSION_TOKEN_BUDGET=${OPENAI_SESSION_TOKEN_BUDGET:-120000}
export PYTHONPATH=.

exec .venv_ai_bridge/bin/python -m ai_bridge.scripts.orchestrator_daemon
