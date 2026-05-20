#!/bin/bash
set -e

# Load environment variables
if [ -f /app/.env ]; then
    source /app/.env
fi

# IMPORTANT SECURITY NOTE:
# Sensitive environment variables (like API tokens, e.g., DESEC_TOKEN, CF_Key)
# should ideally be managed securely. In production, consider using Docker/Podman secrets,
# Kubernetes secrets, or a dedicated secrets management solution instead of
# plain .env files or directly exposing them in docker-compose.yml.
# Ensure .env files are excluded from version control (.gitignore) and have restricted access permissions.

# ========================================
# Logging Functions
# ========================================
log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $*"; }
log_warn() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $*" >&2; }
log_error() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2; }
log_debug() {
    if [ "${DEBUG_MODE}" == "1" ]; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] DEBUG: $*" >&2;
    fi
}

# ========================================
# Main Process
# ========================================
main() {
    log "🚀 Application ready!"
    # Start the node server
    node server.js || { log_error "Node.js server failed to start! Exiting."; exit 1; }
    # Keep the container running if the node server exits, to allow inspection
    # If the Node.js server is meant to be the main process, 'exec' is typically used.
    # For debugging, we remove 'exec' to see if Node.js exits on its own.
    sleep infinity
}

main "$@"