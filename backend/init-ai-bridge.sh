#!/usr/bin/env bash
set -e
export PYTHONPATH=/app:/app/ai_bridge
python3 -m pip install --break-system-packages sqlalchemy psycopg2-binary asyncpg pydantic redis google-genai mistralai pika
# Запускаем созданный демон
exec python3 /app/ai_bridge/scripts/orchestrator_daemon.py
