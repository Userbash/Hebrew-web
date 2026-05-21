#!/bin/bash

# Setup Host Environment for AI Bridge
# This script runs ON THE HOST via the bridge.

echo "Configuring host for AI bridge access..."

# Ensure we can run commands as host user
ID=$(id -u)
USER=$(id -un)

echo "Current host user: $USER (ID: $ID)"

# List of critical tools the AI might need
REQUIRED_TOOLS=("podman" "docker" "systemctl" "git" "npm" "node")

for tool in "${REQUIRED_TOOLS[@]}"; do
    if command -v "$tool" > /dev/null 2>&1; then
        echo "[OK] Found $tool at $(which $tool)"
    else
        echo "[MISSING] $tool is not installed on host"
        # We don't automatically install unless requested, 
        # but we could add logic here to offer installation.
    fi
done

# Check if flatpak permissions are correct (if we were called via flatpak-spawn)
if [ -n "$FLATPAK_ID" ]; then
    echo "Running inside Flatpak: $FLATPAK_ID"
fi

# Create a dedicated 'bridge' directory on host for shared files if needed
mkdir -p "$HOME/.ai_bridge"
echo "Host bridge setup complete."
