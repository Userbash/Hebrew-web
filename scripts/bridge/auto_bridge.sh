#!/bin/bash

# Auto-Bridge System
# Automatically detects and fixes access issues between the isolated IDE and host.

BRIDGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Auto-Bridge Diagnostic..."

# 1. Check isolation type
if [ -f "/.flatpak-info" ]; then
    echo "[INFO] Detected Flatpak isolation."
    
    # 2. Test host spawn
    if flatpak-spawn --host ls / > /dev/null 2>&1; then
        echo "[OK] flatpak-spawn --host is working."
    else
        echo "[ERROR] flatpak-spawn --host failed."
        echo "Attempting to fix permissions..."
        # We can't fix Flatpak permissions from inside the Flatpak easily
        # but we can tell the user how to do it.
        echo "Run this on host: flatpak override --user --talk-name=org.freedesktop.Flatpak $(cat /.flatpak-info | grep 'app-id=' | cut -d= -f2)"
    fi
else
    echo "[INFO] Non-Flatpak or unknown isolation."
fi

# 3. Verify Bridge Scripts
chmod +x "$BRIDGE_DIR"/*.sh

# 4. Initialize whitelist
if [ ! -f "$BRIDGE_DIR/whitelist.txt" ]; then
    echo "[INFO] Initializing whitelist with default tools."
    "$BRIDGE_DIR/exec.sh" --init > /dev/null
fi

# 5. Run Host Side Setup
echo "Running host-side tool check..."
"$BRIDGE_DIR/bridge.sh" bash "$BRIDGE_DIR/setup_host.sh"

echo "Auto-Bridge System Ready."
