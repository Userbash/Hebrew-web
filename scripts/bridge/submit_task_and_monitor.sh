#!/bin/bash
./scripts/bridge/submit_task.sh "$1"
echo "--- ОЖИДАНИЕ ОБРАБОТКИ (Оркестратор: /app/ai_bridge/orchestrator.log) ---"
sleep 2
flatpak-spawn --host podman exec hebrew_ai_backend tail -n 10 /app/ai_bridge/orchestrator.log
