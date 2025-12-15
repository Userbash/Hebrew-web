#!/bin/sh

# Constants
MAX_RETRIES=5
RETRY_DELAY_SECONDS=10
RENEWAL_THRESHOLD_DAYS=30 # Days before expiration to attempt certificate renewal
BACKUP_DIR="/etc/letsencrypt/backup" # Directory for certificate backups

# Logging Functions
log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $*"; }
log_warn() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $*" >&2; }
log_error() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2; }
log_debug() {
    if [ "${DEBUG_MODE}" == "1" ]; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] DEBUG: $*" >&2;
    fi
}

# IP Address Management Functions
get_public_ip() {
    local ip=""
    local attempt=1
    while [ "$attempt" -le "$MAX_RETRIES" ]; do
        log_debug "Attempt $attempt to fetch public IP."
        ip=$(curl -s --max-time 10 https://icanhazip.com || curl -s --max-time 10 https://ident.me)
        if echo "$ip" | grep -E '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'; then
            echo "$ip"
            return 0
        else
            log_warn "Failed to get public IP on attempt $attempt. Response: '$ip'"
            if [ "$attempt" -lt "$MAX_RETRIES" ]; then
                sleep "$RETRY_DELAY_SECONDS"
            fi
        fi
        attempt=$((attempt + 1))
    done
    log_error "Failed to retrieve public IP after $MAX_RETRIES attempts."
    return 1
}

update_desec_a_record() {
    local domain=$1
    local new_ip=$2
    local record_name="" # For root domain
    local rrset_type="A"
    
    log "Attempting to update ${rrset_type} record for ${domain} with IP: ${new_ip}"

    if [ "${DRY_RUN}" == "1" ]; then
        log_warn "[DRY RUN] Would update ${rrset_type} record for ${domain} with IP: ${new_ip}. Returning success."
        return 0
    fi

    local attempt=1
    while [ "$attempt" -le "$MAX_RETRIES" ]; do
        log_debug "DeSEC A record update attempt $attempt/$MAX_RETRIES for domain: $domain"

        local GET_RESPONSE=$(curl -s -X GET \
            -H "Authorization: Token ${DESEC_TOKEN}" \
            "https://desec.io/api/v1/domains/${domain}/rrsets/?subname=${record_name}&type=${rrset_type}")
        
        if [ $? -ne 0 ]; then
            log_error "Failed to fetch existing A records for ${domain} on attempt $attempt. Curl command failed."
            sleep "$RETRY_DELAY_SECONDS"
            attempt=$((attempt + 1))
            continue
        fi

        log_debug "DeSEC GET response for ${domain} A records: ${GET_RESPONSE}"
        
        local current_records=$(echo "$GET_RESPONSE" | jq -r '.[0].records | @json')
        local current_ttl=$(echo "$GET_RESPONSE" | jq -r '.[0].ttl')
        
        if [ "$current_records" == "null" ] || [ -z "$current_records" ]; then
            log_warn "No existing A record found for ${domain}. Creating a new one."
            local CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
                -H "Authorization: Token ${DESEC_TOKEN}" \
                -H "Content-Type: application/json" \
                -d "{\"subname\": \"${record_name}\", \"type\": \"${rrset_type}\", \"ttl\": 3600, \"records\": [\"${new_ip}\"]}" \
                "https://desec.io/api/v1/domains/${domain}/rrsets/")
            
            local HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)
            local BODY=$(echo "$CREATE_RESPONSE" | sed '$d')

            if [ "$HTTP_CODE" -eq 201 ]; then
                log "✅ Successfully created A record for ${domain} with IP: ${new_ip}. "
                return 0
            else
                log_error "Failed to create A record for ${domain} (HTTP $HTTP_CODE) on attempt $attempt. Response: ${BODY}"
            fi
        else
            local existing_ip=$(echo "$current_records" | jq -r '.[0]')
            if [ "$existing_ip" == "$new_ip" ]; then
                log "A record for ${domain} already points to ${new_ip}. No update needed."
                return 0
            fi

            log "Existing A record for ${domain} is ${existing_ip}. Updating to ${new_ip}. "
            
            local PUT_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT \
                -H "Authorization: Token ${DESEC_TOKEN}" \
                -H "Content-Type: application/json" \
                -d "{\"subname\": \"${record_name}\", \"type\": \"${rrset_type}\", \"ttl\": ${current_ttl}, \"records\": [\"${new_ip}\"]}" \
                "https://desec.io/api/v1/domains/${domain}/rrsets/${record_name}/${rrset_type}/")
            
            local HTTP_CODE=$(echo "$PUT_RESPONSE" | tail -n1)
            local BODY=$(echo "$PUT_RESPONSE" | sed '$d')

            if [ "$HTTP_CODE" -eq 200 ]; then
                log "✅ Successfully updated A record for ${domain} to IP: ${new_ip}. "
                return 0
            else
                log_error "Failed to update A record for ${domain} (HTTP $HTTP_CODE) on attempt $attempt. Response: ${BODY}"
            fi
        fi

        if [ "$attempt" -lt "$MAX_RETRIES" ]; then
            log "Retrying in $RETRY_DELAY_SECONDS seconds..."
            sleep "$RETRY_DELAY_SECONDS"
        fi
        attempt=$((attempt + 1))
    done
    
    log_error "Failed to update A record for ${domain} after $MAX_RETRIES attempts."
    return 1
}

check_and_update_ip() {
    log "Initiating IP change detection and DNS update process..."
    
    local current_public_ip=$(get_public_ip)
    if [ $? -ne 0 ]; then
        log_error "Could not retrieve current public IP. Skipping IP update for all domains."
        return 1
    fi
    log "Current public IP detected: ${current_public_ip}"

    for domain_to_check in ${DOMAIN_LIST}; do
        log "Checking IP for domain: ${domain_to_check}"
        local last_ip_file="/etc/letsencrypt/live/${domain_to_check}/.last_ip"
        local last_known_ip=""

        mkdir -p "$(dirname "$last_ip_file")"
        
        if [ -f "$last_ip_file" ]; then
            last_known_ip=$(cat "$last_ip_file")
        fi

        if [ "$current_public_ip" == "$last_known_ip" ]; then
            log "IP for ${domain_to_check} has not changed (${current_public_ip}). No DNS update needed."
        else
            log_warn "IP change detected for ${domain_to_check}: Old IP ${last_known_ip:-"None"} -> New IP ${current_public_ip}. "
            if update_desec_a_record "${domain_to_check}" "${current_public_ip}"; then
                log "Successfully updated DNS A record for ${domain_to_check}. Saving new IP."
                echo "$current_public_ip" > "$last_ip_file"
            else
                log_error "Failed to update DNS A record for ${domain_to_check}. Last known IP not updated."
            fi
        fi
    done
    return 0
}

# Domain & Certificate Management Functions
setup_domain() {
    log "🔍 Preparing to set up domain: ${DOMAIN_NAME}..."
    
    if [ -z "${DOMAIN_NAME}" ]; then
        log_error "DOMAIN_NAME is not set. Cannot set up domain."
        return 1
    fi

    if [ "${DRY_RUN}" == "1" ]; then
        log_warn "[DRY RUN] Would attempt to set up domain '${DOMAIN_NAME}' via deSEC API. Returning success."
        return 0
    fi

    log "Attempting to set up domain '${DOMAIN_NAME}' via deSEC API."
    
    local attempt=1
    while [ "$attempt" -le "$MAX_RETRIES" ]; do
        log_debug "DeSEC API call attempt $attempt for domain: $DOMAIN_NAME"
        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Authorization: Token ${DESEC_TOKEN}" \
            -H "Content-Type: application/json" \
            -d "{\"name\": \"${DOMAIN_NAME}\"}" \
            https://desec.io/api/v1/domains/)
        
        HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
        local BODY=$(echo "$RESPONSE" | sed '$d')

        if [ "$HTTP_CODE" -eq 201 ]; then
            log "✅ Domain '${DOMAIN_NAME}' successfully created on deSEC."
            return 0
        elif [ "$HTTP_CODE" -eq 400 ] && echo "$BODY" | grep -q 'The domain .*	 already exists'; then
            log "⚠️ Domain '${DOMAIN_NAME}' already exists on deSEC. Skipping creation."
            return 0
        else
            log_error "DeSEC API call failed (HTTP $HTTP_CODE) for domain '${DOMAIN_NAME}' on attempt $attempt/$MAX_RETRIES."
            log_debug "Response body: $BODY"
            if [ "$attempt" -lt "$MAX_RETRIES" ]; then
                log "Retrying in $RETRY_DELAY_SECONDS seconds..."
                sleep "$RETRY_DELAY_SECONDS"
            fi
        fi
        attempt=$((attempt + 1))
    done
    
    log_error "Failed to set up domain '${DOMAIN_NAME}' after $MAX_RETRIES attempts."
    return 1
}

setup_certificate() {
    log "🔐 Initiating SSL certificate setup for domain: ${DOMAIN_NAME}..."
    
    if [ -z "${DOMAIN_NAME}" ]; then
        log_error "DOMAIN_NAME is not set. Cannot set up certificate."
        return 1
    fi

    local DOMAIN="${DOMAIN_NAME}"
    local cert_fullchain="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    local cert_privkey="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

    local action_type="none" # Can be "issue" or "renew"

    if [ -f "$cert_fullchain" ] && [ -f "$cert_privkey" ]; then
        log "✅ Existing certificate files found for $DOMAIN."
        local expiration_date_seconds=$(openssl x509 -in "$cert_fullchain" -noout -enddate | sed -e 's/^notAfter=//g' | xargs -I {} date -d {} +%s)
        local current_date_seconds=$(date +%s)
        
        local remaining_seconds=$((expiration_date_seconds - current_date_seconds))
        local remaining_days=$((remaining_seconds / 86400)) # 86400 seconds in a day

        log "Certificate for $DOMAIN expires in $remaining_days days."

        if [ "$remaining_days" -lt "$RENEWAL_THRESHOLD_DAYS" ]; then
            log_warn "Certificate for $DOMAIN is nearing expiration (less than $RENEWAL_THRESHOLD_DAYS days). Attempting to renew."
            action_type="renew"
        else
            log "Certificate for $DOMAIN is still valid. No renewal needed at this time."
            return 0
        fi
    else
        log "No existing certificate found for $DOMAIN. Attempting to issue a new one."
        action_type="issue"
    fi
    
    local attempt=1
    while [ "$attempt" -le "$MAX_RETRIES" ]; do
        log_debug "acme.sh operation attempt $attempt/$MAX_RETRIES for domain: $DOMAIN (Action: ${action_type})"
        
        STAGING_FLAG=""
        if [ "${LE_STAGING}" == "1" ]; then
            STAGING_FLAG="--staging"
            log_warn "Using Let's Encrypt STAGING environment. Certificates will NOT be trusted by browsers."
        fi
        
        DRY_RUN_ACME_FLAG=""
        if [ "${DRY_RUN}" == "1" ]; then
            DRY_RUN_ACME_FLAG="--test"
            log_warn "[DRY RUN] acme.sh will run in test mode. No actual certificate will be issued/renewed."
        fi

        local provider_success=false
        for dns_provider in ${DNS_PROVIDERS}; do
            log_debug "Attempting with DNS provider: $dns_provider"
            
            local provider_ready=true
            case "$dns_provider" in
                "dns_desec")
                    if [ -z "${DESEC_TOKEN}" ]; then
                        log_warn "DESEC_TOKEN not set, skipping dns_desec provider."
                        provider_ready=false
                    fi
                    ;;
                "dns_cf")
                    if [ -z "${CF_Key}" ] || [ -z "${CF_Email}" ]; then
                        log_warn "CF_Key or CF_Email not set, skipping dns_cf provider."
                        provider_ready=false
                    fi
                    ;;
                *)
                    log_warn "Unknown DNS provider specified: $dns_provider. Skipping."
                    provider_ready=false
                    ;;
            esac

            if [ "$provider_ready" = false ]; then
                continue
            fi

            local acme_cmd
            if [ "$action_type" = "renew" ]; then
                # Attempt renewal
                acme_cmd="/usr/local/bin/acme.sh --renew -d \"$DOMAIN\" --home /acme.sh $STAGING_FLAG $DRY_RUN_ACME_FLAG --dns \"$dns_provider\" --reloadcmd \"nginx -s reload\""
            elif [ "$action_type" = "issue" ]; then
                # Attempt issuance
                acme_cmd="/usr/local/bin/acme.sh \
                    --issue \
                    -d \"$DOMAIN\" \
                    -d \"*.$DOMAIN\" \
                    --dns \"$dns_provider\" \
                    --dnssleep 20 \
                    --cert-file \"$cert_fullchain\" \
                    --key-file \"$cert_privkey\" \
                    --fullchain-file \"$cert_fullchain\" \
                    --home /acme.sh \
                    $STAGING_FLAG \
                    $DRY_RUN_ACME_FLAG \
                    --reloadcmd \"nginx -s reload\""
            else
                log_error "Internal logic error: Unknown action_type '${action_type}' for acme.sh command construction."
                continue 2
            fi
            
            log_debug "Executing: $acme_cmd"
            if eval "$acme_cmd"; then
                log "✅ Certificate operation ($([ "$action_type" = "renew" ] && echo "renewal" || echo "issuance")) successful for $DOMAIN using $dns_provider."
                provider_success=true
                break
            else
                log_error "acme.sh operation failed for $DOMAIN using $dns_provider."
            fi
        done

        if [ "$provider_success" = true ]; then
            return 0
        else
            log_error "No DNS provider succeeded for $DOMAIN on attempt $attempt/$MAX_RETRIES."
            if [ "$attempt" -lt "$MAX_RETRIES" ]; then
                log "Retrying full operation in $RETRY_DELAY_SECONDS seconds..."
                sleep "$RETRY_DELAY_SECONDS"
            fi
        fi
        attempt=$((attempt + 1))
    done
    
    log_error "Failed to complete SSL certificate operation for $DOMAIN after $MAX_RETRIES attempts."
    return 1
}

# Function to backup certificates
backup_certificates() {
    log "Initiating certificate backup process..."
    
    if [ "${DRY_RUN}" == "1" ]; then
        log_warn "[DRY RUN] Would perform certificate backup to ${BACKUP_DIR}. Returning success."
        return 0
    fi

    mkdir -p "$BACKUP_DIR"
    if [ $? -ne 0 ]; then
        log_error "Failed to create backup directory: $BACKUP_DIR"
        return 1
    fi

    local timestamp=$(date +%Y%m%d%H%M%S)
    local backup_success=true

    for domain_to_backup in ${DOMAIN_LIST}; do
        local cert_dir="/etc/letsencrypt/live/${domain_to_backup}"
        if [ -d "$cert_dir" ]; then
            local backup_file="${BACKUP_DIR}/${domain_to_backup}_certs_${timestamp}.tar.gz"
            log "Backing up certificates for ${domain_to_backup} to ${backup_file}..."
            if tar -czf "$backup_file" -C "/etc/letsencrypt/live" "${domain_to_backup}"; then
                log "✅ Successfully backed up certificates for ${domain_to_backup}. "
            else
                log_error "Failed to backup certificates for ${domain_to_backup}. "
                backup_success=false
            fi
        else
            log_warn "Certificate directory ${cert_dir} not found for ${domain_to_backup}. Skipping backup for this domain."
        fi
    done

    # Simple retention policy: keep last 7 backups per domain
    for domain_to_clean in ${DOMAIN_LIST}; do
        log_debug "Applying retention policy for ${domain_to_clean}..."
        find "$BACKUP_DIR" -maxdepth 1 -name "${domain_to_clean}_certs_*.tar.gz" | sort -r | sed -n '8,$p' | xargs -r rm -v
    done
    
    if [ "$backup_success" = true ]; then
        log "✅ Certificate backup process completed."
        return 0
    else
        log_error "Certificate backup process completed with errors."
        return 1
    fi
}

# Main logic for cert-manager
cert_manager_main() {
    log_debug "DEBUG: Entering cert_manager_main function."
    if [ -z "${DOMAIN_LIST}" ]; then
        log_error "DOMAIN_LIST environment variable is not set. Please provide a space-separated list of domains."
        exit 1
    fi

    log "Starting certificate management cycle..."

    # IP change detection and DNS A record update
    if ! check_and_update_ip; then
        log_error "IP detection and DNS update failed for one or more domains."
    fi

    for current_domain in ${DOMAIN_LIST}; do
        log "Processing domain: ${current_domain}"
        # Set DOMAIN_NAME for the current iteration (needed by functions)
        export DOMAIN_NAME="${current_domain}" 

        # Ensure domain is registered with deSEC
        if ! setup_domain; then
            log_error "Failed to set up domain ${current_domain}. Skipping certificate setup for this domain."
            continue
        fi

        # Issue or renew certificate
        if ! setup_certificate; then
            log_error "Failed to set up certificate for ${current_domain}. "
        fi
    done

    # Backup certificates after operations
    if ! backup_certificates; then
        log_error "Certificate backup process failed."
    fi

    log "Certificate management cycle completed."
}

# Execute main logic
log_debug "DEBUG: About to call cert_manager_main."
cert_manager_main
