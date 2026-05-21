#!/bin/bash
# Abstracted containerization build script using BridgeOS
BRIDGE_CMD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bridge/exec.sh"

echo "Attempting to build project using BridgeOS..."

echo "Building Backend..."
$BRIDGE_CMD podman build --no-cache -t hebrew-backend -f backend/Dockerfile backend

echo "Building Frontend..."
$BRIDGE_CMD podman build --no-cache -t hebrew-frontend -f frontend-react/Dockerfile frontend-react

echo "Build complete."
