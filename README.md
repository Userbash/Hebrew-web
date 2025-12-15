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
*   **Automated Verification Tests**: Comprehensive system tests to ensure environment and service readiness.

## Technologies Used

### Backend
*   **Node.js**: JavaScript runtime.
*   **Express.js**: Web application framework.
*   **Mongoose**: MongoDB object modeling.
*   **MongoDB**: NoSQL database.
*   **Pino**: Fast Node.js logger.
*   **Jest & Supertest**: Unit, integration, and API testing.

### Frontend
*   **HTML5, CSS3, JavaScript**: Core web technologies.
*   **Nginx**: Web server for serving static files and acting as a reverse proxy.

### DevOps & Tools
*   **Docker & Docker Compose**: Containerization.
*   **GitHub Actions**: CI/CD pipeline automation.
*   **`jq`**: JSON processor for script analysis.
*   **`yaml` & `node-fetch`**: Used by the root test runner for verification.

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Ensure you have the following installed:
*   **Git**: For cloning the repository.
*   **Node.js**: v18.x or higher (includes `npm`).
*   **Docker & Docker Compose**: For containerized development and running services.
*   **`jq`**: JSON processor (used by CI/CD scripts). `sudo apt-get install jq` on Debian/Ubuntu.

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/Hebrew-web.git # Replace with actual repo URL
    cd Hebrew-web
    ```

2.  **Setup Environment Variables**:
    Create a `.env` file in the project root by copying from `.env.example`:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file and fill in the necessary environment variables, especially for the database connection and ports.

3.  **Install Backend Dependencies**:
    ```bash
    npm install --prefix backend
    ```

4.  **Install Root Test Runner Dependencies**:
    ```bash
    npm install
    ```

## Running the Project

### Development Mode (using Docker Compose)

The easiest way to run the full application (backend, frontend/Nginx, and MongoDB) in a development environment is using Docker Compose.

1.  **Start Services**:
    ```bash
    docker compose up --build
    ```
    This will build the Docker images (if not already built or if Dockerfiles have changed) and start all services defined in `docker-compose.yml`.

2.  **Access the Application**:
    Once services are running, the frontend should be accessible via your browser, typically at `http://localhost:80` or the `NGINX_PORT` specified in your `.env` file.

3.  **Stop Services**:
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

These tests verify the overall project setup, Docker Compose configuration, path integrity, and Nginx detection.

```bash
npm test # Runs the master test runner at the root
```
This command executes `tests/run-all-tests.js`, which orchestrates several checks.

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
│   └── NGINX_CONFIG.md      # Nginx configuration notes
├── docker-compose.yml       # Defines multi-service Docker application
├── .env.example             # Example environment variables
├── .gitignore               # Git ignored files
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                  # Project license
├── package.json             # Root package.json for system-level tests and tools
├── package-lock.json        # Lock file for root dependencies
└── README.md                # Project README (this file)
```

## Deployment

The `deploy.sh` script and Docker setup provide the foundation for deployment. Further configuration (e.g., Kubernetes manifests, cloud provider specifics) would be necessary for a full production deployment. The CI/CD pipeline can be extended to automate deployment to various environments based on branch pushes.

## Contribution

Contributions are welcome! Please refer to `CONTRIBUTING.md` for guidelines.

## License

This project is licensed under the [ISC License](LICENSE).