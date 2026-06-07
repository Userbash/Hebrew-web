#!/bin/bash
set -euo pipefail

BRIDGE_CMD="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/ai_bridge/scripts/bridge/exec.sh"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BACKEND_IMAGE="localhost/hebrew-backend:latest"
FRONTEND_IMAGE="localhost/hebrew-frontend:latest"
ORCHESTRATOR_IMAGE="localhost/hebrew-orchestrator:latest"
PG_VOLUME_NAME="${PG_VOLUME_NAME:-hebrew_pgdata}"
REDIS_VOLUME_NAME="${REDIS_VOLUME_NAME:-hebrew_redisdata}"
AVATAR_VOLUME_NAME="${AVATAR_VOLUME_NAME:-hebrew_avatar_uploads}"
JWT_SECRET="${JWT_SECRET:-dev_local_jwt_secret_2026_change_me}"
BACKEND_PORT="${BACKEND_PORT:-3001}"
FRONTEND_PORT="${FRONTEND_PORT:-8081}"
ORCHESTRATOR_PORT="${ORCHESTRATOR_PORT:-8000}"
ORCHESTRATOR_ENV_ARGS=()
if [ -f "$PROJECT_ROOT/.env.bridge" ]; then
  ORCHESTRATOR_ENV_ARGS+=(--env-file "$PROJECT_ROOT/.env.bridge")
fi
if [ -f "$PROJECT_ROOT/.env.gemini.local" ]; then
  ORCHESTRATOR_ENV_ARGS+=(--env-file "$PROJECT_ROOT/.env.gemini.local")
fi

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

assert_port_free() {
  local port="$1"
  local owner=""
  owner="$(ss -ltn 2>/dev/null | awk '{print $4}' | grep -E ":${port}$" || true)"
  if [ -n "$owner" ]; then
    echo "[ERROR] Port ${port} is already in use. Stop conflicting process/container and retry."
    exit 1
  fi
}

echo "Starting project containers manually via BridgeOS..."
validate_secret

if ! image_exists "$BACKEND_IMAGE"; then
  echo "[ERROR] Backend image is missing: $BACKEND_IMAGE"
  echo "Run: bash scripts/build_abstracted.sh"
  exit 1
fi

if ! image_exists "$FRONTEND_IMAGE"; then
  echo "[ERROR] Frontend image is missing: $FRONTEND_IMAGE"
  echo "Run: bash scripts/build_abstracted.sh"
  exit 1
fi

if ! image_exists "$ORCHESTRATOR_IMAGE"; then
  echo "[ERROR] Orchestrator image is missing: $ORCHESTRATOR_IMAGE"
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
$BRIDGE_CMD podman rm -f hebrew_ai_frontend hebrew_ai_backend hebrew_ai_orchestrator hebrew_ai_redis hebrew_ai_postgres >/dev/null 2>&1 || true

assert_port_free "$BACKEND_PORT"
assert_port_free "$FRONTEND_PORT"
assert_port_free "$ORCHESTRATOR_PORT"

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

echo "Starting Orchestrator..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_orchestrator \
  --security-opt no-new-privileges \
  --network hebrew-net \
  -p ${ORCHESTRATOR_PORT}:8000 \
  "${ORCHESTRATOR_ENV_ARGS[@]}" \
  -e PYTHONPATH=/app \
  -e AI_BRIDGE_API_ENABLED=1 \
  -e AI_BRIDGE_AUTOSTART_LOCAL_LLM="${AI_BRIDGE_AUTOSTART_LOCAL_LLM:-false}" \
  -e AI_BRIDGE_LIVE_MODEL_PROBE="${AI_BRIDGE_LIVE_MODEL_PROBE:-false}" \
  -e AI_BRIDGE_LOCAL_LLM_AUTO_PROVISION="${AI_BRIDGE_LOCAL_LLM_AUTO_PROVISION:-true}" \
  -e AI_BRIDGE_REQUIRE_EXTERNAL_SCANNERS="${AI_BRIDGE_REQUIRE_EXTERNAL_SCANNERS:-false}" \
  -e AI_BRIDGE_MEMORY_ENABLED="${AI_BRIDGE_MEMORY_ENABLED:-true}" \
  -e AI_BRIDGE_MEMORY_DATABASE_URL="${AI_BRIDGE_MEMORY_DATABASE_URL:-postgresql+asyncpg://postgres:postgres123@hebrew_ai_postgres:5432/hebrew_ai_db}" \
  "$ORCHESTRATOR_IMAGE"

echo "Starting Backend..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_backend \
  --security-opt no-new-privileges \
  --network hebrew-net \
  -p ${BACKEND_PORT}:3001 \
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
  -e ORCHESTRATOR_BRIDGE_URL="${ORCHESTRATOR_BRIDGE_URL:-http://host.containers.internal:${ORCHESTRATOR_PORT}}" \
  -e AI_BRIDGE_OPENAI_AUTO_MODEL="${AI_BRIDGE_OPENAI_AUTO_MODEL:-true}" \
  -e OPENAI_SESSION_TOKEN_BUDGET="${OPENAI_SESSION_TOKEN_BUDGET:-120000}" \
  -v "$AVATAR_VOLUME_NAME":/app/public/uploads/avatars:Z \
  -v "$PROJECT_ROOT/ai_bridge":/app/ai_bridge:Z \
  -v "$PROJECT_ROOT/.agent":/app/.agent:Z \
  -v "$PROJECT_ROOT/memory_store":/app/memory_store:Z \
  "$BACKEND_IMAGE"

echo "Starting Frontend..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_frontend \
  --security-opt no-new-privileges \
  --network hebrew-net \
  -p ${FRONTEND_PORT}:80 \
  "$FRONTEND_IMAGE"

wait_http_ok "orchestrator" "http://127.0.0.1:${ORCHESTRATOR_PORT}/health" 45
wait_http_ok "backend" "http://127.0.0.1:${BACKEND_PORT}/api/health" 45
wait_http_ok "frontend" "http://127.0.0.1:${FRONTEND_PORT}" 30
wait_http_ok "frontend-api-proxy" "http://127.0.0.1:${FRONTEND_PORT}/api/health" 30

echo "Containers started."
echo "Backend: http://localhost:${BACKEND_PORT}"
echo "Frontend: http://localhost:${FRONTEND_PORT}"
echo "Orchestrator: http://localhost:${ORCHESTRATOR_PORT}"
