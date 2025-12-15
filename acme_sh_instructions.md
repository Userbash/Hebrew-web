To enable `acme.sh` for obtaining a certificate and specifying an external domain, please follow these steps:

**1. Obtain a `DESEC_TOKEN`:**
   - Go to [deSEC.io](https://desec.io/) and create an account.
   - Follow their instructions to generate an API token (DESEC_TOKEN).

**2. Configure a `DOMAIN_NAME`:**
   - Register a domain name that you own (e.g., `yourdomain.com`).
   - Configure this domain to use deSEC's nameservers.
   - For `acme.sh` to successfully obtain a certificate, the `DOMAIN_NAME` specified must be a publicly resolvable domain that is managed by your deSEC account. `localhost` will not work.

**3. Update your `.env` file:**
   - Edit the `.env` file in the project root to include your actual `DESEC_TOKEN` and `DOMAIN_NAME`.
     ```
     NGINX_PORT=8080
     NGINX_HTTPS_PORT=8443
     DOMAIN_NAME=yourdomain.com  # Replace with your actual domain
     DB_USER=postgres
     DB_PASSWORD=postgres123
     DB_NAME=hebrew_ai_db
     DB_PORT=5432
     BACKEND_PORT=3001
     DESEC_TOKEN=YOUR_ACTUAL_DESEC_TOKEN  # Replace with your deSEC API token
     ACME_EMAIL=your_email@example.com    # Replace with your email
     ```

**4. Re-enable `acme.sh` functionality in `scripts/entrypoint.sh`:**
   - Edit `scripts/entrypoint.sh` and uncomment the `setup_domain` and `setup_certificate` calls in the `main` function.
     ```bash
     # Main process
     main() {
         setup_domain
         setup_certificate
         log "🚀 Application ready!"
         # Start the node server
         exec node server.js
     }
     ```

**5. Re-add `certs` volume mounts to `docker-compose.yml`:**
   - Edit `docker-compose.yml` and add the `certs` volume back to both the `backend` and `nginx` services.

   For the `backend` service:
   ```yaml
       backend:
         # ... other configurations ...
         volumes:
           - certs:/etc/letsencrypt # Add this line
         entrypoint: ["bash", "/usr/local/bin/entrypoint.sh"]
         restart: unless-stopped
   ```

   For the `nginx` service:
   ```yaml
       nginx:
         # ... other configurations ...
         volumes:
           - certs:/etc/letsencrypt:ro # Add this line
         # ... other configurations ...
   ```

**6. Re-enable HTTPS `server` block in `frontend/nginx.conf.template`:**
   - Edit `frontend/nginx.conf.template` and uncomment the `server` block that listens on port `443` (HTTPS) and all its related SSL directives, and the proxy headers inside the location block.

**7. Bring down, rebuild, and bring up services:**
   - After making these changes, run the following commands:
     ```bash
     podman-compose down
     podman-compose build
     podman-compose up -d
     ```

After these steps, `acme.sh` should attempt to obtain a certificate for your specified domain, and Nginx should be configured to use it. You can then check the logs of the `backend` and `nginx` containers for success or any further issues related to certificate issuance.

This concludes the full pipeline verification cycle on the local system. I have successfully built the entire project, ensured all services are running, and passed all tests on the local system, and provided instructions for enabling external domain and `acme.sh` functionality.
