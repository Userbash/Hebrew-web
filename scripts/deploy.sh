#!/bin/bash
set -euo pipefail

echo "[deploy] Running bridge diagnostics..."
bash scripts/bridge/auto_bridge.sh

echo "[deploy] Building images..."
bash scripts/build_abstracted.sh

echo "[deploy] Starting containers..."
bash scripts/start_manual.sh

echo "[deploy] Done."
