#!/bin/bash
# Manual container startup script using BridgeOS
BRIDGE_CMD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bridge/exec.sh"

echo "Starting project containers manually via BridgeOS..."

# 1. Create Network
echo "Creating network..."
$BRIDGE_CMD podman network create hebrew-net || true

# 2. Start Postgres
echo "Starting Postgres..."
$BRIDGE_CMD podman run -d \
  --name hebrew_ai_postgres \
  --network hebrew-net \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -e POSTGRES_DB=hebrew_ai_db \
  postgres:16-alpine

# 3. Start Redis
echo "Starting Redis..."
$BRIDGE_CMD podman run -d \
  --name hebrew_ai_redis \
  --network hebrew-net \
  redis:7-alpine

# 4. Start Backend
echo "Starting Backend..."
$BRIDGE_CMD podman run -d \
  --name hebrew_ai_backend \
  --network hebrew-net \
  -p 3001:3001 \
  -e NODE_ENV=production \
  -e PORT=3001 \
  -e DB_HOST=hebrew_ai_postgres \
  -e DB_PORT=5432 \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres123 \
  -e DB_NAME=hebrew_ai_db \
  -e REDIS_HOST=hebrew_ai_redis \
  -e REDIS_PORT=6379 \
  hebrew-backend:latest

# 5. Start Frontend
echo "Starting Frontend..."
$BRIDGE_CMD podman run -d \
  --name hebrew_ai_frontend \
  --network hebrew-net \
  -p 8081:80 \
  hebrew-frontend:latest

echo "Containers started."
echo "Backend: http://localhost:3001"
echo "Frontend: http://localhost:8081"
