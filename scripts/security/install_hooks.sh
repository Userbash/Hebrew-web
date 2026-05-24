#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

git config core.hooksPath .githooks
chmod +x .githooks/pre-push scripts/security/prepush_secret_scan.sh

echo "[hooks] Installed. core.hooksPath=.githooks"
echo "[hooks] pre-push secret scan is active"
