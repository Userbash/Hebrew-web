# Hebrew Web Application (AI-Enhanced)

## Project Overview

This project is a full-stack web application designed for learning Hebrew, featuring a Node.js backend with an Express API and a frontend serving static HTML, CSS, and JavaScript. The project emphasizes automated testing, Docker-based deployment, and a robust CI/CD pipeline with self-healing capabilities, heavily influenced by an AI-driven development and testing methodology.

## Features

*   **Interactive Hebrew Lessons**: Frontend pages for interactive lessons.
*   **Dictionary Functionality**: Dedicated page for Hebrew dictionary.
*   **Quizzes**: Interactive quizzes to test knowledge.
*   **User Profiles & Progress Tracking**: Manage user accounts and track learning progress.
*   **RESTful API**: Node.js/Express backend providing data and logic.
*   **Containerized Development & Deployment**: Full Docker and Docker Compose support for isolated environments.
*   **Automated CI/CD**: GitHub Actions pipeline for continuous integration, testing, and potential deployment, incorporating AI-driven analysis and self-healing.
*   **Automated DNS+SSL Certificate Management**: Integrates `acme.sh` with `cert-manager` service for automated certificate issuance, renewal, and DNS record updates.

## Technologies Used

### Backend
*   **Node.js**: JavaScript runtime.
*   **Express.js**: Web application framework.
*   **PostgreSQL**: Relational database for persistent data storage.
*   **Redis**: In-memory data store, used for caching and session management.
*   **Pino**: Fast Node.js logger.
*   **Jest & Supertest**: Unit, integration, and API testing.

### Frontend
*   **HTML5, CSS3, JavaScript**: Core web technologies.
*   **Nginx**: Web server for serving static files and acting as a reverse proxy for the backend API.

### DevOps & Tools
*   **Docker & Docker Compose**: Containerization.
*   **GitHub Actions**: CI/CD pipeline automation.
*   **`jq`**: JSON processor for script analysis.
*   **`yaml` & `node-fetch`**: Dependencies for project-wide utilities and system tests, used by the root test runner for verification.

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Ensure you have the following installed:
*   **Git**: For cloning the repository.
*   **Node.js**: v18.x or higher (includes `npm`).
*   **Docker & Docker Compose**: For containerized development and running services (or **Podman & Podman Compose** if preferred, especially on Linux).
*   **`jq`**: JSON processor (used by CI/CD scripts). `sudo apt-get install jq` on Debian/Ubuntu.

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-organization/hebrew-web-app.git
    cd hebrew-web-app
    ```

2.  **Setup Environment Variables**:
    Create a `.env` file in the project root by copying from `.env.example`:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file and fill in the necessary environment variables. Below is a guide for the critical DNS/SSL related variables:

    *   **`DESEC_TOKEN`**: Your API token for deSEC.io. Required for `dns_desec` provider. Obtain from [deSEC.io](https://desec.io/).
    *   **`DOMAIN_LIST`**: A space-separated list of domain(s) for which you want to manage certificates (e.g., `"yourdomain.com www.yourdomain.com"`). Ensure these domains are configured to use your chosen DNS provider's nameservers.
    *   **`ACME_EMAIL`**: A valid email address for Let's Encrypt notifications.
    *   **`LE_STAGING`**: Set to `1` to use the Let's Encrypt staging environment for testing (recommended). Set to `0` for production certificates.
    *   **`DRY_RUN`**: Set to `1` to simulate `acme.sh` operations and deSEC API calls without making actual changes (recommended for testing). Set to `0` to enable actual certificate issuance/updates.
    *   **`DNS_PROVIDERS`**: A space-separated list of `acme.sh` DNS API providers to use, in order of preference (e.g., `"dns_desec dns_cf"`). Defaults to `dns_desec`.
    *   **`CF_Key`**, **`CF_Email`**: Required if using `dns_cf` (Cloudflare) as a DNS provider.
    *   Also, ensure database connection and ports are configured as needed.

3.  **Install Dependencies**:
    *   **Backend**:
        ```bash
        npm install --prefix backend
        ```
    *   **Root (Test Runner & Utilities)**:
        ```bash
        npm install
        ```

## Automated DNS+SSL Certificate Management

This project now includes a comprehensive, automated system for managing DNS records and SSL/TLS certificates, designed to enhance the reliability, security, and automation of the Hebrew-web project's infrastructure. This system replaces manual certificate handling with a robust, containerized solution built around \`acme.sh\` and orchestrated via \`podman-compose\` (or \`docker-compose\`).

### How it Works:

A dedicated \`cert-manager\` Docker service (using the official \`neilpang/acme.sh:latest\` image) runs the \`scripts/run_cert_manager.sh\` script. This script handles:
1.  **IP Change Detection**: Monitors the server's public IP and updates DNS A/AAAA records via your configured DNS provider (e.g., deSEC).
2.  **Domain Setup**: Ensures your domain is registered with the DNS provider's API.
3.  **Certificate Issuance/Renewal**: Uses \`acme.sh\` to obtain or renew SSL/TLS certificates from Let's Encrypt (or other ACME CAs) using DNS challenges.
4.  **Automatic Backups**: Creates timestamped backups of certificates.
5.  **Graceful Error Handling**: Includes retry logic for failed API calls.
6.  **Dry-Run Mode**: Allows testing the entire process without actual changes.

### Essential Setup Steps for Certificate Management:

To obtain real, trusted SSL certificates and ensure your application is accessible via HTTPS, follow these steps:

1.  **Configure DNS Provider**:
    *   **deSEC (Recommended)**: Go to [deSEC.io](https://desec.io/), create an account, register your domain(s), and configure them to use deSEC's nameservers. Generate an API token (\`DESEC_TOKEN\`).
    *   **Other Providers**: If using a different DNS provider supported by \`acme.sh\` (e.g., Cloudflare), ensure you have the necessary API credentials (e.g., \`CF_Key\`, \`CF_Email\`).

2.  **Update \`.env\` file (Project Root)**:
    Ensure the following environment variables are correctly set in your \`.env\` file:
    *   \`DESEC_TOKEN\`: Your deSEC API token (or equivalent for your chosen DNS provider).
    *   \`DOMAIN_LIST\`: Your actual domain(s) (e.g., \`"yourdomain.com www.yourdomain.com"\`).
    *   \`ACME_EMAIL\`: A valid email address for Let's Encrypt notifications.
    *   \`LE_STAGING\`: Set to \`0\` for production certificates. (Keep as \`1\` for initial testing to avoid rate limits).
    *   \`DRY_RUN\`: Set to \`0\` to enable actual certificate issuance/updates. (Keep as \`1\` for initial testing).
    *   \`DNS_PROVIDERS\`: Specify your preferred DNS providers, e.g., \`"dns_desec"\` or \`"dns_desec dns_cf"\`.

3.  **Enable HTTPS for Nginx**:
    *   The \`frontend/nginx.conf.template\` includes a commented-out \`server\` block for HTTPS (listening on port \`443\`). Uncomment this block and its related SSL directives once you have obtained certificates. This typically happens after the first successful run of the \`cert-manager\`.
    *   Ensure the \`ports\` section for the \`nginx\` service in \`docker-compose.yml\` has \`- "8443:443"\` uncommented.

4.  **Initial Certificate Issuance (One-time Setup)**:
    *   Run your services using \`podman-compose up -d\` (or \`docker-compose up -d\`).
    *   The \`cert-manager\` service will automatically attempt to obtain certificates.
    *   Monitor the \`cert-manager\` logs: \`podman-compose logs -f cert-manager\`.
    *   Once successful, your certificates will be stored in the \`certs\` Docker volume.

5.  **Continuous Renewal**:
    The \`cert-manager\` service is configured to restart on failure, and its internal script is designed to check and renew certificates automatically when they are nearing expiration. You can implement a separate cron job or systemd timer to periodically trigger the \`cert-manager\` service to run its script.

    **Note**: For production environments, consider using Docker/Podman secrets or a dedicated secrets management solution for sensitive credentials like \`DESEC_TOKEN\` and other API keys.

## Running the Project

### Development Mode (using Docker Compose)

The easiest way to run the full application (backend, frontend/Nginx, and all supporting services like Postgres, Redis, and the `cert-manager`) in a development environment is using Docker Compose.

1.  **Start Services**:
    ```bash
    docker compose up --build -d
    ```
    This will build the Docker images (if not already built or if Dockerfiles have changed) and start all services defined in `docker-compose.yml` in detached mode.

2.  **Monitor `cert-manager` (Optional, but Recommended)**:
    For the first run, it's highly recommended to monitor the `cert-manager` logs to ensure certificates are being processed as expected:
    ```bash
    docker compose logs -f cert-manager
    ```
    Once certificates are issued (or dry-run completes), you can stop monitoring.

3.  **Access the Application**:
    Once services are running, the frontend should be accessible via your browser, typically at `http://localhost:8080` (or the `NGINX_PORT` specified in your `.env` file) for HTTP. For HTTPS, it will be `https://localhost:8443` (or `NGINX_HTTPS_PORT`).

4.  **Stop Services**:
    ```bash
    docker compose down
    ```

## Testing

The project includes unit, integration, and comprehensive system verification tests.

### Backend Tests (Unit & Integration)

Run Jest tests for the Node.js backend:
```bash
npm test --prefix backend         # Run all backend tests
npm run test:coverage --prefix backend # Run backend tests with coverage report
```

### System Verification Tests

These tests verify the overall project setup, Docker Compose (or Podman Compose) configuration, path integrity, Nginx detection, and full container deployment.

```bash
npm test # Runs the master test runner at the root
```
This command executes `tests/run-all-tests.js`, which orchestrates several checks, including the Podman deployment test (`tests/system/test-deployment-podman.sh`) if Podman and `podman-compose` are installed and configured.

### CI/CD Pipeline

The project is configured with a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that automatically runs on pushes to `main` and `develop` branches. This pipeline includes:
*   Dependency installation and security audit.
*   Docker image builds.
*   Automated unit, integration, and system verification tests.
*   AI-driven error analysis and self-healing attempts for common issues (e.g., `ECONNREFUSED`, `MODULE_NOT_FOUND`, `TIMEOUT`, `OUT_OF_MEMORY`).
*   Automated re-testing after self-healing.
*   Comprehensive reporting in GitHub Action summaries and artifacts.

## Project Structure

```
.
├── .github/                 # GitHub Actions workflows
├── backend/                 # Node.js Express API
│   ├── api/                 # API routes, middleware, data models
│   ├── public/              # Backend-served assets (if any)
│   ├── tests/               # Backend unit and integration tests
│   ├── Dockerfile           # Dockerfile for backend service
│   └── package.json         # Backend dependencies and scripts
├── frontend/                # Static frontend assets
│   ├── public/              # HTML pages, CSS, JS
│   ├── Dockerfile           # Dockerfile for Nginx (serving frontend)
│   └── nginx.conf.template  # Nginx configuration
├── scripts/                 # Utility scripts (deployment, entrypoint, system detection)
│   ├── entrypoint.sh        # Docker container entrypoint
│   ├── deploy.sh            # Deployment script (high-level)
│   └── detect_system.sh     # System detection utility
├── tests/                   # Root-level system verification tests
│   ├── system/              # Individual system test modules
│   └── run-all-tests.js     # Master test runner script
├── docs/                    # Project documentation
│   ├── agent/               # AI Agent internal documentation (Commands, Testing Guide, Quick Start)
│   ├── NGINX_CONFIG.md      # Nginx configuration notes
│   └── acme_sh_instructions.md # Instructions for enabling acme.sh and external domain access
├── docker-compose.yml       # Defines multi-service Docker application
├── .env.example             # Example environment variables
├── .gitignore               # Git ignored files
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                  # Project license
├── package.json             # Root package.json for project-wide utilities, system-level tests, and tools.
├── package-lock.json        # Lock file for root dependencies
└── README.md                # Project README (this file)
```

## Deployment

The `deploy.sh` script and Docker setup provide the foundation for deployment. Further configuration (e.g., Kubernetes manifests, cloud provider specifics) would be necessary for a full production deployment. The CI/CD pipeline can be extended to automate deployment to various environments based on branch pushes.

## Contribution

Contributions are welcome! Please refer to `CONTRIBUTING.md` for guidelines.

## License

This project is licensed under the [MIT License](LICENSE).