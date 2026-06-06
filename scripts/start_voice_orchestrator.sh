#!/bin/bash
set -euo pipefail

# Script to start the Orchestrator as a background voice assistant

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo " Starting AI Orchestrator with Voice Listener"
echo "=============================================="

# Ensure system audio dependencies are installed (requires sudo, uncomment if needed)
# echo "[Setup] Checking for PortAudio..."
# sudo apt-get update && sudo apt-get install -y portaudio19-dev python3-pyaudio

# Virtual environment check
if [[ -d ".venv_ai_bridge" ]]; then
    echo "[Setup] Activating virtual environment..."
    source .venv_ai_bridge/bin/activate
fi

# Enable Voice Module in the Orchestrator
export AI_BRIDGE_ENABLE_VOICE=true
export AI_BRIDGE_AUTOSTART_LOCAL_LLM=true

# Fix API Port collision (Container uses 8000)
DEFAULT_API_PORT="${AI_BRIDGE_API_PORT:-8001}"
CHOSEN_API_PORT="$DEFAULT_API_PORT"
while ! python3 - "$CHOSEN_API_PORT" <<'PYPORT'
import socket
import sys
port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("0.0.0.0", port))
    except OSError:
        raise SystemExit(1)
raise SystemExit(0)
PYPORT
do
    CHOSEN_API_PORT="$((CHOSEN_API_PORT + 1))"
done
export AI_BRIDGE_API_PORT="$CHOSEN_API_PORT"
echo "[Setup] API port: $AI_BRIDGE_API_PORT"

# Fix Ollama Endpoint (Script runs on Host, not inside Docker)
export AI_BRIDGE_LOCAL_LLM_ENDPOINT="${AI_BRIDGE_LOCAL_LLM_ENDPOINT:-http://127.0.0.1:11434}"

# Launch the orchestrator in bridge mode so it stays resident
echo "[Start] Initializing Core..."
python3 -m ai_bridge.scripts.run_orchestrator --use-bridge
