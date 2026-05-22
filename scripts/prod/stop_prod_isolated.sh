#!/bin/bash
set -euo pipefail
BRIDGE_CMD="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/bridge/exec.sh"

$BRIDGE_CMD podman rm -f hebrew_ai_edge hebrew_ai_admin_frontend hebrew_ai_frontend hebrew_ai_backend hebrew_ai_redis hebrew_ai_postgres >/dev/null 2>&1 || true
$BRIDGE_CMD podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
