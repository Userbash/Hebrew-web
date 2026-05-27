#!/usr/bin/env bash
set -e
export PYTHONPATH=/app:/app/ai_bridge
# Install full AI bridge runtime dependencies used by orchestrator modules.
python3 -m pip install --break-system-packages -r /app/ai_bridge/requirements-ai.txt
python3 -m pip install --break-system-packages sqlalchemy psycopg2-binary asyncpg
# Start orchestrator daemon
exec python3 /app/ai_bridge/scripts/orchestrator_daemon.py
