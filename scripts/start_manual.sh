#!/bin/bash
# Manual container startup script using BridgeOS
BRIDGE_CMD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bridge/exec.sh"

echo "Starting project containers manually via BridgeOS..."

PG_VOLUME_NAME="${PG_VOLUME_NAME:-hebrew_pgdata}"
REDIS_VOLUME_NAME="${REDIS_VOLUME_NAME:-hebrew_redisdata}"
AVATAR_VOLUME_NAME="${AVATAR_VOLUME_NAME:-hebrew_avatar_uploads}"

# 1. Create Network
echo "Creating network..."
$BRIDGE_CMD podman network create hebrew-net || true

echo "Ensuring persistent volumes..."
$BRIDGE_CMD podman volume create "$PG_VOLUME_NAME" >/dev/null || true
$BRIDGE_CMD podman volume create "$REDIS_VOLUME_NAME" >/dev/null || true
$BRIDGE_CMD podman volume create "$AVATAR_VOLUME_NAME" >/dev/null || true

# 2. Start Postgres
echo "Starting Postgres..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_postgres \
  --network hebrew-net \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -e POSTGRES_DB=hebrew_ai_db \
  -v "$PG_VOLUME_NAME":/var/lib/postgresql/data:Z \
  --security-opt no-new-privileges \
  postgres:16-alpine

# 3. Start Redis
echo "Starting Redis..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_redis \
  --network hebrew-net \
  -v "$REDIS_VOLUME_NAME":/data:Z \
  --security-opt no-new-privileges \
  redis:7-alpine

# 4. Start Backend
echo "Starting Backend..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_backend \
  --security-opt no-new-privileges \
  --network hebrew-net \
  -p 3001:3001 \
  -e NODE_ENV=production \
  -e PORT=3001 \
  -e JWT_SECRET="${JWT_SECRET:-dev_local_jwt_secret_2026_change_me}" \
  -e DB_HOST=hebrew_ai_postgres \
  -e DB_PORT=5432 \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres123 \
  -e DB_NAME=hebrew_ai_db \
  -e REDIS_HOST=hebrew_ai_redis \
  -e REDIS_PORT=6379 \
  -v "$AVATAR_VOLUME_NAME":/app/public/uploads/avatars:Z \
  hebrew-backend:latest

# 5. Start Frontend
echo "Starting Frontend..."
$BRIDGE_CMD podman run -d --pull=never \
  --name hebrew_ai_frontend \
  --security-opt no-new-privileges \
  --network hebrew-net \
  -p 8081:80 \
  hebrew-frontend:latest

echo "Containers started."
echo "Backend: http://localhost:3001"
echo "Frontend: http://localhost:8081"
