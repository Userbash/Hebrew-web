#!/bin/bash
# Script to automatically verify and repair AI provider stack

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "   AI Provider Stack Maintainer & Repair"
echo "=============================================="

# 1. Antigravity (agy)
echo -n "[Check] Antigravity CLI (agy)... "
if flatpak-spawn --host agy --version &>/dev/null; then
    echo -e "${GREEN}INSTALLED${NC}"
    # Check if authorized
    if flatpak-spawn --host python3 ai_bridge/scripts/antigravity_login.py --verify &>/dev/null; then
        echo -e "${GREEN}[OK] Antigravity is authorized${NC}"
    else
        echo -e "${YELLOW}[WARN] Antigravity not authorized. Starting login flow...${NC}"
        flatpak-spawn --host python3 ai_bridge/scripts/antigravity_login.py --login --timeout 300
    fi
else
    echo -e "${RED}NOT FOUND${NC}"
    echo "Please ensure 'agy' (Antigravity CLI) is installed on the host."
fi

# 2. Sourcecraft (src)
echo -n "[Check] Sourcecraft CLI (src)... "
SRC_BIN="./.tooling/sourcecraft/bin/src"
if [[ -x "$SRC_BIN" ]]; then
    echo -e "${GREEN}FOUND${NC}"
else
    echo -e "${RED}MISSING${NC}"
    echo "Sourcecraft binary not found in $SRC_BIN"
fi

# 3. API Keys (Mistral & Codex)
echo "[Check] API Keys..."
if [[ -f ".env.bridge" ]]; then
    # Parse .env.bridge manually since it might have export or just key=val
    M_KEY=$(grep "MISTRAL_API_KEY" .env.bridge | cut -d'=' -f2)
    O_KEY=$(grep "OPENAI_API_KEY" .env.bridge | cut -d'=' -f2)
    
    if [[ -n "$M_KEY" ]]; then
        echo -e "  - Mistral: ${GREEN}OK${NC}"
    else
        echo -e "  - Mistral: ${RED}MISSING KEY${NC}"
    fi
    if [[ -n "$O_KEY" ]]; then
        echo -e "  - Codex (OpenAI): ${GREEN}OK${NC}"
    else
        echo -e "  - Codex (OpenAI): ${RED}MISSING KEY${NC}"
    fi
else
    echo -e "${RED}.env.bridge not found${NC}"
fi

# 4. Local LLM (Ollama)
echo -n "[Check] Local LLM (Ollama)... "
if curl -s http://127.0.0.1:11434/api/tags &>/dev/null; then
    echo -e "${GREEN}RUNNING${NC}"
else
    echo -e "${YELLOW}NOT RESPONDING${NC}"
    echo "Note: Ensure Ollama is running on 127.0.0.1:11434 if local models are used."
fi

# 5. Core Connection
echo -n "[Check] Orchestrator Core... "
CORE_URL=""
if curl -s http://localhost:8000/stats &>/dev/null; then
    CORE_URL="http://localhost:8000"
elif curl -s http://localhost:8001/stats &>/dev/null; then
    CORE_URL="http://localhost:8001"
fi

if [[ -n "$CORE_URL" ]]; then
    echo -e "${GREEN}CONNECTED ($CORE_URL)${NC}"
else
    echo -e "${YELLOW}OFFLINE${NC}"
    echo "Starting Orchestrator..."
    ./scripts/start_ai_bridge_stack.sh
fi

echo "=============================================="
echo "   Repair Complete"
echo "=============================================="
