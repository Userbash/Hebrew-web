# Hebrew AI 2025

Hebrew AI is a modern learning platform designed for high-performance and secure Hebrew language education. This project features a React-based frontend and a robust Node.js/TypeScript backend, backed by a replicated PostgreSQL database and Redis caching.

## Key Features

- **Secure Architecture**: All host operations are abstracted through a secure bridge (BridgeOS), allowing the project to run safely in isolated development environments.
- **Data Integrity**: Replicated PostgreSQL setup with Master-Replica architecture ensures data durability and high availability.
- **Optimized Search**: Blazing fast full-text search using PostgreSQL GIN indexes and `tsvector`.
- **Modern Security**: 
  - JWT-based session management.
  - High-security password hashing using `bcrypt` (factor 12).
  - Strict SQL parameterization to prevent injection attacks.
  - UUID-based entity identification.

## Project Structure

```text
├── backend/            # TypeScript Node.js API
│   ├── database/       # Migrations and schema
│   └── api/            # Routes, middleware, and controllers
├── frontend-react/     # Vite + React + Tailwind CSS
├── scripts/            # DevOps and orchestration scripts
│   ├── bridge/         # Secure host-to-IDE bridge (BridgeOS)
│   └── start_manual.sh # Manual container orchestration
└── docker-compose.yml  # Deployment configuration
```

## Getting Started

### 1. Prerequisites

Ensure you have `podman` or `docker` installed on your host machine.

### 2. Initialize BridgeOS

Since the development environment is isolated, you must initialize the bridge to grant access to host utilities:

```bash
bash scripts/bridge/auto_bridge.sh
```

### 3. Setup Database

Initialize the replicated database infrastructure:

```bash
bash scripts/start_replicated_db.sh
```

### 4. Build and Launch

Build the container images and start the services:

```bash
bash scripts/build_abstracted.sh
bash scripts/start_manual.sh
```

The application will be available at:
- **Frontend**: [http://localhost:8081](http://localhost:8081)
- **Backend API**: [http://localhost:3001](http://localhost:3001)

## Development

To add new host-machine commands to the allowed list, update the whitelist:

```bash
echo "command_name" >> scripts/bridge/whitelist.txt
```

## Security Disclosure

This project implements strict isolation. All communication with the host machine is audited through `scripts/bridge/exec.sh`. Direct execution of host commands from within the container is disabled by design.
