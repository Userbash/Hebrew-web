#!/usr/bin/env sh
set -e

export PYTHONPATH=/app
export AI_BRIDGE_AUTOSTART_LOCAL_LLM=true
cd /app

exec python3 -m ai_bridge.scripts.orchestrator_daemon
