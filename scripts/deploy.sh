#!/bin/bash
set -euo pipefail

python3 -m ai_bridge.scripts.pre_deploy_security_check

echo "[deploy] Running bridge diagnostics..."
bash scripts/bridge/exec.sh --init

echo "[deploy] Building images..."
bash scripts/build_abstracted.sh

echo "[deploy] Starting containers..."
bash scripts/start_manual.sh

echo "[deploy] Done."
