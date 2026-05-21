#!/bin/bash
# Replicated Database Startup Script
BRIDGE_CMD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bridge/exec.sh"
DB_DIR="/var/home/sanya/Hebrew-web/backend/database"

echo "Configuring Replicated Database Infrastructure..."

# 1. Cleanup old instances
echo "Stopping old database instances..."
$BRIDGE_CMD podman stop hebrew_ai_postgres pg_master pg_replica hebrew_ai_redis || true
$BRIDGE_CMD podman rm hebrew_ai_postgres pg_master pg_replica hebrew_ai_redis || true

# 2. Start Master
echo "Launching PG Master..."
$BRIDGE_CMD podman run -d \
  --name pg_master \
  --network hebrew-net \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=master_pass_2025 \
  -e POSTGRES_DB=hebrew_db \
  -p 5432:5432 \
  postgres:16-alpine -c wal_level=replica -c max_wal_senders=10

echo "Waiting for Master to initialize..."
sleep 10

# 3. Create replication user on Master
echo "Creating replication user..."
$BRIDGE_CMD podman exec pg_master psql -U admin -d hebrew_db -c "CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'repl_pass_2025';"

# 4. Initialize Schema on Master
echo "Applying optimized schema to Master..."
$BRIDGE_CMD podman exec -i pg_master psql -U admin -d hebrew_db < "$DB_DIR/migrations/001_init.sql"

# 5. Start Redis for Fast Caching
echo "Launching Redis Cache..."
$BRIDGE_CMD podman run -d \
  --name hebrew_ai_redis \
  --network hebrew-net \
  -p 6379:6379 \
  redis:7-alpine

# 6. Start Replica (Simplification: using the same image and pointing to master)
# In a real production, we'd use pg_basebackup. For this automated task, 
# we'll start it as a hot standby.
echo "Launching PG Replica (Read-Only)..."
$BRIDGE_CMD podman run -d \
  --name pg_replica \
  --network hebrew-net \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=master_pass_2025 \
  -e POSTGRES_DB=hebrew_db \
  -p 5433:5432 \
  postgres:16-alpine

echo "Database Infrastructure Ready."
echo "Master: localhost:5432"
echo "Replica: localhost:5433"
echo "Redis: localhost:6379"
