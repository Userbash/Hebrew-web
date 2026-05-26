#!/usr/bin/env bash
# Unified start script for AI Orchestrator with integrated API Bridge

set -e

# Navigate to project root if script is run from scripts/
cd "$(dirname "$0")/.."

echo "=== AI Orchestrator Unified Launcher ==="

# 1. Environment Check
if [ ! -f ".env.bridge" ]; then
    echo "[!] .env.bridge not found. Creating default..."
    cat > .env.bridge <<EOF
QUEUE_FILE=.agent/bridge_queue.json
RESULTS_DIR=.agent/bridge_results
CHAT_TIMEOUT=30.0
POLLING_INTERVAL=0.5
BRIDGE_HOST=0.0.0.0
BRIDGE_PORT=8000
BRIDGE_URL=http://localhost:8000
USER_ID=engineer_sanya
EOF
fi

# 2. Dependencies
echo "[*] Checking dependencies..."
python3 -m pip install -q -r ai_bridge/requirements-ai.txt

# 3. Cleanup old files
echo "[*] Cleaning up old queue and results..."
mkdir -p .agent/bridge_results
rm -f .agent/bridge_queue.json

# 4. Start Core (Daemon mode)
echo "[*] Starting Orchestrator Core with integrated API..."
export PYTHONPATH=$PYTHONPATH:.
python3 ai_bridge/scripts/orchestrator_daemon.py &
CORE_PID=$!

echo "[+] Orchestrator is running (PID: $CORE_PID)"
echo "[+] HTTP API is available at http://localhost:8000/chat"
echo ""
echo "You can now run: python3 ai_bridge/scripts/chat_console.py"
echo "To stop everything, run: kill $CORE_PID"

# Keep the script alive if not running in background
wait $CORE_PID
