#!/usr/bin/env sh
set -e

export PYTHONPATH=/app
cd /app

exec python3 -m ai_bridge.scripts.orchestrator_daemon
