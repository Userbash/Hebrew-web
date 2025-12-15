#!/bin/bash
set -e

# Load environment variables
if [ -f /app/.env ]; then
    source /app/.env
fi

# Log function
log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }

# Function to setup domain
setup_domain() {
    log "🔍 Checking for domain..."
    
    if [ -f /etc/letsencrypt/.domain ]; then
        DOMAIN_NAME=$(cat /etc/letsencrypt/.domain)
        log "✅ Domain found: $DOMAIN_NAME"
        return 0
    fi
    
    log "📝 Creating new domain via API..."
    
    # API call to deSEC
    RESPONSE=$(curl -s -X POST \
        -H "Authorization: Token ${DESEC_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"${DOMAIN_NAME}\"}" \
        https://desec.io/api/v1/domains/)
    
    if echo "$RESPONSE" | grep -q '"name"'; then
        log "✅ Domain created: $DOMAIN_NAME"
        echo "$DOMAIN_NAME" > /etc/letsencrypt/.domain
    else
        log "⚠️  Domain already exists or error: $RESPONSE"
        echo "$DOMAIN_NAME" > /etc/letsencrypt/.domain
    fi
}

# Function to issue SSL certificate
setup_certificate() {
    log "🔐 Issuing SSL certificate..."
    
    DOMAIN=$(cat /etc/letsencrypt/.domain)
    
    if [ -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
        log "✅ Certificate already exists."
        return 0
    fi
    
    # Issue certificate via Let's Encrypt
    STAGING_FLAG=""
    if [ "${LE_STAGING}" == "1" ]; then
        STAGING_FLAG="--staging"
    fi
    
    /acme.sh/acme.sh \
        --issue \
        -d "$DOMAIN" \
        -d "*.$DOMAIN" \
        --dns dns_desec \
        --dnssleep 20 \
        --cert-file /etc/letsencrypt/live/$DOMAIN/cert.pem \
        --key-file /etc/letsencrypt/live/$DOMAIN/privkey.pem \
        --fullchain-file /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
        $STAGING_FLAG
    
    log "✅ Certificate issued successfully."
}

# Main process
main() {
    setup_domain
    setup_certificate
    log "🚀 Application ready!"
    # Start the node server
    exec node server.js
}

main "$@"
