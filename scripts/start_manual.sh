#!/bin/bash
set -euo pipefail

BRIDGE_CMD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bridge/exec.sh"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BACKEND_IMAGE="localhost/hebrew-backend:latest"
FRONTEND_IMAGE="localhost/hebrew-frontend:latest"
PG_VOLUME_NAME="${PG_VOLUME_NAME:-hebrew_pgdata}"
REDIS_VOLUME_NAME="${REDIS_VOLUME_NAME:-hebrew_redisdata}"
AVATAR_VOLUME_NAME="${AVATAR_VOLUME_NAME:-hebrew_avatar_uploads}"
JWT_SECRET="${JWT_SECRET:-dev_local_jwt_secret_2026_change_me}"

wait_http_ok() {
  local name="$1"
  local url="$2"
  local attempts="${3:-30}"
  local i=1
  while [ "$i" -le "$attempts" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[OK] $name is healthy: $url"
      return 0
    fi
    sleep 1
    i=$((i + 1))
  done
  echo "[ERROR] $name healthcheck failed: $url"
  return 1
}

image_exists() {
  "$BRIDGE_CMD" podman image exists "$1"
}

validate_secret() {
  if [ "${#JWT_SECRET}" -lt 24 ]; then
    echo "[ERROR] JWT_SECRET must be at least 24 characters"
    exit 1
  fi
}

echo "Starting project containers manually via BridgeOS..."
validate_secret

if [[ ! -d "$PROJECT_ROOT/backend" ]] && ! image_exists "$BACKEND_IMAGE"; then
  echo "[ERROR] Backend source directory is missing: $PROJECT_ROOT/backend"
  echo "[ERROR] Backend image is also missing: $BACKEND_IMAGE"
  echo "Run build after restoring backend sources."
  exit 1
fi

if ! image_exists "$FRONTEND_IMAGE"; then
  echo "[ERROR] Frontend image is missing: $FRONTEND_IMAGE"
  echo "Run: bash scripts/build_abstracted.sh"
  exit 1
fi

echo "Creating network..."
$BRIDGE_CMD podman network create hebrew-net || true

echo "Ensuring persistent volumes..."
$BRIDGE_CMD podman volume create "$PG_VOLUME_NAME" >/dev/null || true
$BRIDGE_CMD podman volume create "$REDIS_VOLUME_NAME" >/dev/null || true
$BRIDGE_CMD podman volume create "$AVATAR_VOLUME_NAME" >/dev/null || true

echo "Removing old containers if present..."
$BRIDGE_CMD podman rm -f hebrew_ai_frontend hebrew_ai_backend hebrew_ai_redis hebrew_ai_postgres >/dev/null 2>&1 || true

echo "Starting Postgres..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_postgres \
  --network hebrew-net \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -e POSTGRES_DB=hebrew_ai_db \
  -v "$PG_VOLUME_NAME":/var/lib/postgresql/data:Z \
  --security-opt no-new-privileges \
  docker.io/library/postgres:16-alpine

echo "Starting Redis..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_redis \
  --network hebrew-net \
  -v "$REDIS_VOLUME_NAME":/data:Z \
  --security-opt no-new-privileges \
  docker.io/library/redis:7-alpine

echo "Starting Backend..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_backend \
  --security-opt no-new-privileges \
  --network hebrew-net \
  -p 3001:3001 \
  -e NODE_ENV=production \
  -e PORT=3001 \
  -e JWT_SECRET="$JWT_SECRET" \
  -e DB_HOST=hebrew_ai_postgres \
  -e DB_PORT=5432 \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres123 \
  -e DB_NAME=hebrew_ai_db \
  -e REDIS_HOST=hebrew_ai_redis \
  -e REDIS_PORT=6379 \
  -v "$AVATAR_VOLUME_NAME":/app/public/uploads/avatars:Z \
  "$BACKEND_IMAGE"

echo "Starting Frontend..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_frontend \
  --security-opt no-new-privileges \
  --network hebrew-net \
  -p 8081:80 \
  "$FRONTEND_IMAGE"

wait_http_ok "backend" "http://127.0.0.1:3001/api/health" 45
wait_http_ok "frontend" "http://127.0.0.1:8081" 30
wait_http_ok "frontend-api-proxy" "http://127.0.0.1:8081/api/health" 30

echo "Containers started."
echo "Backend: http://localhost:3001"
echo "Frontend: http://localhost:8081"
