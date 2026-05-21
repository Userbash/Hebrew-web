#!/bin/bash

# Bridge Manager - A unified interface for running commands on the host machine
# from within an isolated environment (Flatpak/Container).

BRIDGE_LOG="/var/tmp/bridge_access.log"
CONFIG_FILE="$HOME/.bridge_config"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_access() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] COMMAND: $@" >> "$BRIDGE_LOG"
}

detect_bridge_method() {
    if [ -f "/.flatpak-info" ]; then
        echo "flatpak-spawn"
    elif [ -n "$IS_CONTAINER" ] || [ -f "/.dockerenv" ]; then
        echo "ssh" # Or other method
    else
        echo "direct"
    fi
}

run_on_host() {
    local method=$(detect_bridge_method)
    log_access "$@"

    case "$method" in
        "flatpak-spawn")
            flatpak-spawn --host "$@"
            ;;
        "direct")
            "$@"
            ;;
        *)
            echo -e "${RED}Error: No supported bridge method found.${NC}"
            return 1
            ;;
    esac
}

# Fix permissions or install missing tools on host
auto_repair() {
    local tool=$1
    echo -e "${YELLOW}Attempting to repair access for tool: $tool${NC}"
    
    # Example: if tool is missing, try to find it or install it
    if ! run_on_host which "$tool" > /dev/null 2>&1; then
        echo -e "${YELLOW}Tool $tool not found on host. Attempting discovery...${NC}"
        # This part can be expanded to use dnf/apt/etc on host
        run_on_host sudo dnf install -y "$tool" || run_on_host sudo apt-get install -y "$tool"
    fi
}

# Main entry point
if [ "$1" == "--repair" ]; then
    auto_repair "$2"
elif [ "$#" -gt 0 ]; then
    run_on_host "$@"
else
    echo "Usage: $0 [command] [args...]"
    echo "       $0 --repair [tool_name]"
fi
