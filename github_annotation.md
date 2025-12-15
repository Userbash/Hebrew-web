# Automated DNS + SSL Certificate Management System for Hebrew-web

This repository now includes a comprehensive, automated system for managing DNS records and SSL/TLS certificates, designed to enhance the reliability, security, and automation of the Hebrew-web project's infrastructure. This system replaces manual certificate handling with a robust, containerized solution built around `acme.sh` and orchestrated via `podman-compose` (or `docker-compose`).

## Features and Enhancements:

*   **Dedicated `cert-manager` Service:**
    *   A new `cert-manager` Docker service, based on the official `neilpang/acme.sh:latest` image, handles all certificate lifecycle operations. This decouples certificate management from the main `backend` application, improving modularity and security.
    *   Centralized logic in `scripts/run_cert_manager.sh` for all certificate-related tasks.

*   **Robust Certificate Automation:**
    *   **Error Recovery & Retries:** Automatic retry mechanisms with configurable delays and maximum attempts are implemented for all external API calls (deSEC, Let's Encrypt), ensuring resilience against transient network or service failures.
    *   **Enhanced Logging:** Introduced structured logging functions (`log`, `log_warn`, `log_error`, `log_debug`) for clear, timestamped output, aiding in diagnostics and troubleshooting.
    *   **Proactive Renewal:** Certificates are automatically monitored for expiration. The system intelligently triggers renewal if a certificate is nearing its expiry date (within `RENEWAL_THRESHOLD_DAYS`).
    *   **Multi-Domain Support:** Easily manage SSL certificates for multiple domains or subdomains by configuring a single `DOMAIN_LIST` environment variable.
    *   **Dynamic IP Updates:** The system detects changes in the server's public IP address and automatically updates DNS A records via the deSEC API, ensuring continuous domain resolution.
    *   **Alternative DNS Provider Fallback:** Configured `setup_certificate` to iterate through a `DNS_PROVIDERS` list, allowing fallback options (e.g., `dns_desec`, `dns_cf`) if a primary DNS provider fails or is not configured.
    *   **Dry-Run Mode:** A `DRY_RUN` environment variable enables testing the entire certificate issuance and DNS update process without making actual changes, crucial for safe configuration validation.
    *   **Automatic Backups:** Certificates and critical configuration files are automatically backed up as timestamped `tar.gz` archives with a simple retention policy.

*   **Infrastructure Optimization:**
    *   **Streamlined `backend` Service:** The `backend` Dockerfile is now cleaner, focusing solely on the Node.js application's runtime dependencies, as `acme.sh` and its complexities are offloaded to the `cert-manager`.
    *   **`podman-compose` Compatibility:** The entire setup is verified and optimized for `podman-compose`.
    *   **Secure Credential Handling:** Best practices for managing sensitive environment variables (like API tokens) are highlighted.

## CI/CD Pipeline Reliability Improvements:

*   **Resolved Backend Test Failures:** Addressed "mocha: not found" errors during backend testing by explicitly adding \`mocha\` as a development dependency in \`backend/package.json\`. This ensures all necessary test tools are available during CI/CD runs.
*   **Fixed Docker Image Build Failures:** Corrected \`COPY\` commands within \`backend/Dockerfile\` to properly reference \`package*.json\` files and the application code relative to the build context. This ensures the backend Docker image builds successfully without pathing errors.

## Verification:

The comprehensive pipeline verification cycle using `podman-compose` confirmed that all services build, start, and run correctly. The `cert-manager` service successfully executes the `acme.sh` dry-run logic, demonstrating proper communication with Let's Encrypt staging and policy enforcement for placeholder domains. Frontend Nginx access on port 80 was also verified.