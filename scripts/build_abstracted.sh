#!/bin/bash
# Abstracted containerization build script
PODMAN_CMD="/usr/bin/flatpak-spawn --host podman"

echo "Attempting to build project using abstracted Podman..."

if ! $PODMAN_CMD --version > /dev/null 2>&1; then
    echo "Error: Podman not accessible via flatpak-spawn. Please check environment permissions."
    exit 1
fi

echo "Building Backend..."
$PODMAN_CMD build --no-cache -t hebrew-backend -f backend/Dockerfile backend
echo "Building Frontend..."
$PODMAN_CMD build --no-cache -t hebrew-frontend -f frontend/Dockerfile frontend

echo "Build complete."
