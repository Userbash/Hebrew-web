#!/usr/bin/env bash
set -euo pipefail

echo "[CHECK] Detecting host bridge"

if command -v flatpak-spawn >/dev/null 2>&1; then
  HOST="flatpak-spawn --host"
else
  HOST=""
fi

check_cmd() {
  echo "[CHECK] $1"
  $HOST which "$1" || echo "[WARN] $1 not found"
}

check_cmd node
check_cmd npx
check_cmd podman

echo "[CHECK] podman info"
$HOST podman info || echo "[WARN] podman unavailable"

echo "[CHECK] podman socket"
$HOST systemctl --user status podman.socket || true

echo "[DONE] bridge check completed"
