#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${AI_BRIDGE_LOCAL_LLM_CONTAINER:-ai-kernel-local}"
MODEL_NAME="${AI_BRIDGE_LOCAL_LLM_MODEL:-qwen2.5:32b-instruct-q4_k_m}"
OLLAMA_PORT="${AI_BRIDGE_LOCAL_LLM_PORT:-11434}"

log() { echo "[LLM-INTEGRATION] $1"; }

require_binary() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "ERROR: required binary '$1' is not installed on the host." >&2
        exit 1
    fi
}

require_binary distrobox
require_binary python3

if ! distrobox list --no-color | grep -q "${CONTAINER_NAME}"; then
    log "Creating distrobox ${CONTAINER_NAME}..."
    distrobox create --name "${CONTAINER_NAME}" --image docker.io/library/debian:bookworm --yes --nvidia --additional-flags "--publish ${OLLAMA_PORT}:${OLLAMA_PORT}"
fi

log "Installing Ollama inside ${CONTAINER_NAME}..."
distrobox enter "${CONTAINER_NAME}" -- bash -lc "set -euo pipefail; export DEBIAN_FRONTEND=noninteractive; apt-get update; apt-get install -y curl ca-certificates python3-pip; curl -fsSL https://ollama.com/install.sh | sh"

log "Starting Ollama service and pulling ${MODEL_NAME}..."
distrobox enter "${CONTAINER_NAME}" -- bash -lc "set -euo pipefail; OLLAMA_HOST=0.0.0.0 OLLAMA_ORIGINS='*' nohup ollama serve > /tmp/ollama.log 2>&1 & sleep 5; ollama pull ${MODEL_NAME}"

log "Verifying bridge on 127.0.0.1:${OLLAMA_PORT}..."
python3 - "${MODEL_NAME}" "${OLLAMA_PORT}" <<'PY'
import json
import sys
import urllib.request

model_name = sys.argv[1]
port = sys.argv[2]
url = f"http://127.0.0.1:{port}/api/tags"
with urllib.request.urlopen(url, timeout=10) as response:
    payload = json.load(response)
models = payload.get("models", []) if isinstance(payload, dict) else []
model_names = {item.get("name", "") for item in models if isinstance(item, dict)}
if model_name not in model_names:
    raise SystemExit(f"model {model_name} not found in {url}")
print(f"Model {model_name} is ready at {url}")
PY
