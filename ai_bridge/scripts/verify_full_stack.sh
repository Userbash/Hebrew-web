#!/usr/bin/env bash
set -e

echo "=== FULL STACK API VERIFICATION ==="

check_endpoint() {
  local name="$1"
  local url="$2"
  echo -n "[CHECK] $name ($url)... "
  if curl -fsS "$url" >/dev/null 2>&1; then
    echo "✅ OK"
  else
    echo "❌ FAILED"
  fi
}

check_endpoint "Backend API Health" "http://localhost:3001/api/health"
check_endpoint "Main Frontend" "http://localhost:8081"
check_endpoint "Admin Frontend" "http://localhost:8082"
check_endpoint "Loki Ready" "http://localhost:3100/ready"
check_endpoint "AI Orchestrator" "http://localhost:8000/chat"

echo "=== CONTAINER STATUS ==="
flatpak-spawn --host podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
