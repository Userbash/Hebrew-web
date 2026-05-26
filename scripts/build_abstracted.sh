#!/bin/bash
set -euo pipefail

BRIDGE_CMD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bridge/exec.sh"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend-react"
BACKEND_IMAGE="localhost/hebrew-backend:latest"
FRONTEND_IMAGE="localhost/hebrew-frontend:latest"

echo "Attempting to build project using BridgeOS..."

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "[ERROR] Backend directory not found: $BACKEND_DIR"
  exit 1
fi

if [[ ! -f "$BACKEND_DIR/Dockerfile" ]]; then
  echo "[ERROR] Backend Dockerfile not found: $BACKEND_DIR/Dockerfile"
  exit 1
fi

if [[ ! -f "$BACKEND_DIR/server.ts" || ! -f "$BACKEND_DIR/package.json" ]]; then
  echo "[ERROR] Backend directory structure is invalid: expected server.ts and package.json in $BACKEND_DIR"
  echo "[ERROR] Renaming or moving backend directory is not allowed."
  exit 1
fi

if [[ ! -f "$FRONTEND_DIR/Dockerfile" ]]; then
  echo "[ERROR] Frontend Dockerfile not found: $FRONTEND_DIR/Dockerfile"
  exit 1
fi

echo "Building Backend image: $BACKEND_IMAGE"
"$BRIDGE_CMD" podman build --no-cache --format docker -t "$BACKEND_IMAGE" -f "$BACKEND_DIR/Dockerfile" "$PROJECT_ROOT"

echo "Building Frontend image: $FRONTEND_IMAGE"
"$BRIDGE_CMD" podman build --no-cache --format docker -t "$FRONTEND_IMAGE" -f "$FRONTEND_DIR/Dockerfile" "$FRONTEND_DIR"

echo "Build complete."
