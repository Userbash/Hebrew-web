#!/bin/bash
set -euo pipefail

BRIDGE_CMD="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/bridge/exec.sh"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

APP_DOMAIN_NAME="${APP_DOMAIN_NAME:-app.local}"
ADMIN_DOMAIN_NAME="${ADMIN_DOMAIN_NAME:-admin.local}"
ADMIN_ALLOW_CIDR="${ADMIN_ALLOW_CIDR:-127.0.0.1/32}"
JWT_SECRET="${JWT_SECRET:-change_me_prod_secret}"
PG_VOLUME_NAME="${PG_VOLUME_NAME:-hebrew_pgdata}"
REDIS_VOLUME_NAME="${REDIS_VOLUME_NAME:-hebrew_redisdata}"
AVATAR_VOLUME_NAME="${AVATAR_VOLUME_NAME:-hebrew_avatar_uploads}"
CERTS_DIR="${CERTS_DIR:-$PROJECT_ROOT/infra/edge/certs}"

BACKEND_IMAGE="localhost/hebrew-backend:latest"
FRONTEND_IMAGE="localhost/hebrew-frontend:latest"

EDGE_CONF_TEMPLATE="$PROJECT_ROOT/infra/edge/nginx.prod.conf.template"
EDGE_CONF_RENDERED="$PROJECT_ROOT/infra/edge/nginx.prod.conf"

image_exists() {
  "$BRIDGE_CMD" podman image exists "$1"
}

validate_required_env() {
  if [ "${#JWT_SECRET}" -lt 32 ]; then
    echo "[prod] ERROR: JWT_SECRET must be at least 32 characters"
    exit 1
  fi

  if [ "$APP_DOMAIN_NAME" = "app.local" ] || [ "$ADMIN_DOMAIN_NAME" = "admin.local" ]; then
    echo "[prod] ERROR: APP_DOMAIN_NAME/ADMIN_DOMAIN_NAME must be real domains in production"
    exit 1
  fi
}

echo "[prod] Validating required env..."
validate_required_env

echo "[prod] Rendering edge config..."
mkdir -p "$CERTS_DIR"

if [[ ! -f "$CERTS_DIR/fullchain.pem" || ! -f "$CERTS_DIR/privkey.pem" ]]; then
  echo "[prod] ERROR: TLS cert files not found in $CERTS_DIR"
  echo "Required files: fullchain.pem and privkey.pem"
  exit 1
fi

sed \
  -e "s|\${APP_DOMAIN_NAME}|$APP_DOMAIN_NAME|g" \
  -e "s|\${ADMIN_DOMAIN_NAME}|$ADMIN_DOMAIN_NAME|g" \
  -e "s|\${ADMIN_ALLOW_CIDR}|$ADMIN_ALLOW_CIDR|g" \
  "$EDGE_CONF_TEMPLATE" > "$EDGE_CONF_RENDERED"

echo "[prod] Building backend/frontend images..."
cd "$PROJECT_ROOT"
bash scripts/build_abstracted.sh

if ! image_exists "$BACKEND_IMAGE" || ! image_exists "$FRONTEND_IMAGE"; then
  echo "[prod] ERROR: required images are missing after build"
  exit 1
fi

echo "[prod] Creating isolated network and volumes..."
$BRIDGE_CMD podman network create hebrew-net || true
$BRIDGE_CMD podman volume create "$PG_VOLUME_NAME" >/dev/null || true
$BRIDGE_CMD podman volume create "$REDIS_VOLUME_NAME" >/dev/null || true
$BRIDGE_CMD podman volume create "$AVATAR_VOLUME_NAME" >/dev/null || true

echo "[prod] Stopping old containers if present..."
$BRIDGE_CMD podman rm -f hebrew_ai_edge hebrew_ai_admin_frontend hebrew_ai_frontend hebrew_ai_backend hebrew_ai_redis hebrew_ai_postgres >/dev/null 2>&1 || true

echo "[prod] Starting postgres/redis/backend/frontend/admin (no host port exposure)..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_postgres \
  --network hebrew-net \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -e POSTGRES_DB=hebrew_ai_db \
  -v "$PG_VOLUME_NAME":/var/lib/postgresql/data:Z \
  --security-opt no-new-privileges \
  docker.io/library/postgres:16-alpine

$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_redis \
  --network hebrew-net \
  -v "$REDIS_VOLUME_NAME":/data:Z \
  --security-opt no-new-privileges \
  docker.io/library/redis:7-alpine

$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_backend \
  --network hebrew-net \
  --security-opt no-new-privileges \
  -e NODE_ENV=production \
  -e PORT=3001 \
  -e BACKEND_PORT=3001 \
  -e JWT_SECRET="$JWT_SECRET" \
  -e DB_HOST=hebrew_ai_postgres \
  -e DB_PORT=5432 \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres123 \
  -e DB_NAME=hebrew_ai_db \
  -e REDIS_HOST=hebrew_ai_redis \
  -e REDIS_PORT=6379 \
  -e CORS_ORIGINS="https://$APP_DOMAIN_NAME,https://$ADMIN_DOMAIN_NAME" \
  -v "$AVATAR_VOLUME_NAME":/app/public/uploads/avatars:Z \
  "$BACKEND_IMAGE"

$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_frontend \
  --network hebrew-net \
  --security-opt no-new-privileges \
  "$FRONTEND_IMAGE"

$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_admin_frontend \
  --network hebrew-net \
  --security-opt no-new-privileges \
  "$FRONTEND_IMAGE"

echo "[prod] Starting edge proxy (only 80/443 exposed)..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_edge \
  --network hebrew-net \
  --security-opt no-new-privileges \
  -p 80:80 \
  -p 443:443 \
  -v "$EDGE_CONF_RENDERED":/etc/nginx/nginx.conf:ro,Z \
  -v "$CERTS_DIR":/etc/nginx/certs:ro,Z \
  docker.io/library/nginx:1.27-alpine

echo "[prod] Done. Published ports should be only 80/443 on edge container."
$BRIDGE_CMD podman ps --format 'table {{.Names}}\t{{.Ports}}'
