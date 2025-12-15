# Hebrew AI 2025

A modern, production-ready Hebrew language learning platform with automated testing and deployment infrastructure.

## Features

- **Automated Domain and SSL:** Automatically registers a free domain with deSEC.io and obtains an SSL certificate from Let's Encrypt.
- **Backend API** - Node.js Express server with modern middleware serving both the API and the frontend
- **PostgreSQL** - Persistent data storage
- **Redis** - Caching layer
- **Nginx** - Reverse proxy & load balancing for frontend and backend
- **Automated Testing** - Comprehensive test suite for various components
- **Smart Deployment** - Automated script for easy setup and deployment

## Quick Start

### Prerequisites
- **Containerization Tool:** Either Docker Desktop (includes `docker` and `docker compose` plugin) OR Podman (with `podman-compose` installed).
    - If you need help installing these, please refer to the `installation_recommendations.md` file in the project root.
- Node.js 18+ (for local development and running specific tests)
- A deSEC.io account and API token. Get one at [desec.io](https://desec.io/).
- 2GB free disk space

### Deploy in 30 Seconds

```bash
# 1. Clone the repository
git clone https://github.com/your-username/hebrew-ai-2025.git
cd hebrew-ai-2025

# 2. Copy and configure environment variables
cp .env.example .env
# Open .env and set your DESEC_TOKEN, DOMAIN_NAME, and ACME_EMAIL.

# 3. Deploy
# This script will auto-detect Docker or Podman and use the appropriate compose commands.
./deploy.sh
```

### Access the Application

- **Application:** `https://your-domain-name`
- **Backend API:** `https://your-domain-name/api/`
- **Health Check:** `https://your-domain-name/api/health`

## Project Structure

```
hebrew-ai-2025/
├── .github/                       # GitHub Actions workflows
├── docker-compose.yml             # Docker Compose configuration (primary deployment)
├── .env.example                   # Environment variables example
├── .gitignore                     # Git ignore rules
├── LICENSE                        # Project license
├── README.md                      # Project documentation (this file)
├── CONTRIBUTING.md                # Contribution guidelines
├── deploy.sh                      # Deployment script
├── installation_recommendations.md # Auto-generated recommendations for container tools
├── tests/                         # Top-level project tests
│   ├── run-all-tests.js
│   ├── nginx-detection.test.js
│   ├── backend-verification.test.js
│   └── test-deployment-podman.sh
│
├── backend/                       # Backend service (Node.js Express API)
│   ├── Dockerfile                 # Dockerfile for the backend service
│   ├── package.json               # Backend dependencies and scripts
│   ├── server.js                  # Main backend application file
│   ├── api/                       # API routes, middleware, data
│   │   ├── data/
│   │   ├── middleware/
│   │   └── routes/
│   └── tests/                     # Backend specific tests
│       ├── quick-test.js
│       └── test-api.js
│
├── frontend/                      # Frontend static assets (served by Nginx)
│   ├── Dockerfile                 # Dockerfile for the Nginx frontend server
│   ├── nginx.conf.template        # Nginx configuration template for frontend
│   ├── public/                    # Actual static files (HTML, CSS, JS)
│   │   ├── css/
│   │   ├── js/
│   │   └── pages/
│   └── package.json               # Frontend specific package.json (if used for build process)
│
└── scripts/                       # Utility scripts
    └── entrypoint.sh              # Entrypoint script for cert-manager
```

## Configuration

### Environment Variables

Create `.env` from `.env.example` and fill in the values:

```bash
# Domain and SSL Configuration
# Get your deSEC.io token from https://desec.io/
DESEC_TOKEN=
# Your domain name. It will be created if it doesn't exist.
# Must be a sub-domain of a domain you own in deSEC.io (e.g. myapp.dedyn.io)
DOMAIN_NAME=
# Your email address for Let's Encrypt
ACME_EMAIL=
# Set to 1 to use Let's Encrypt staging environment for testing
LE_STAGING=0

# Database
DB_USER=postgres
DB_PASSWORD=secure_password_here
DB_NAME=hebrew_ai_db
DB_PORT=5432

# Backend
BACKEND_PORT=3001
NODE_ENV=production

# Nginx
NGINX_PORT=80
NGINX_HTTPS_PORT=443

# External Nginx (auto-detected - leave empty if using internal Nginx)
EXTERNAL_NGINX=false
```

## Deployment

The `deploy.sh` script automates the build and deployment process. It will automatically detect if Docker or Podman are installed and use the appropriate `compose` commands.

```bash
./deploy.sh
```
- Builds images
- Starts containers
- Runs health checks
- Automatically registers a domain and obtains an SSL certificate.

### Running with Tests

You can run the deployment followed by the comprehensive test suite:

```bash
./deploy.sh
node tests/run-all-tests.js
```

## Development

### Running Tests
```bash
# Run all verification tests
node tests/run-all-tests.js

# Test specific components
node tests/nginx-detection.test.js
node tests/backend-verification.test.js
node tests/docker-compose-validator.test.js

# Full Podman deployment test (requires Podman & podman-compose installed)
# Ensure PROJECT_ROOT is correctly set in test-deployment-podman.sh if running directly.
./tests/test-deployment-podman.sh
```

### View Logs
```bash
# All services (command determined by deploy.sh)
<compose_command> logs -f

# Specific service (e.g., backend)
<compose_command> logs -f backend
```
*(Replace `<compose_command>` with `docker compose` or `podman-compose` depending on your setup)*

### Manage Services
```bash
# Stop services
<compose_command> down

# Stop and remove volumes
<compose_command> down -v

# Restart specific service
<compose_command> restart backend

# View service status
<compose_command> ps

# Resource usage (replace <container_tool> with 'docker' or 'podman')
<container_tool> stats
```

## Troubleshooting

### Port Already in Use
```bash
# Check which process is using the port
ss -tuln | grep :80

# Change port in .env and restart
<compose_command> down
<compose_command> up -d
```

### Backend Connection Error
```bash
# Check logs
<compose_command> logs backend

# Verify health
curl https://your-domain-name/api/health

# Restart service
<compose_command> restart backend
```

### Build Issues
```bash
# Force rebuild
<compose_command> build --no-cache

# Check build logs
<compose_command> build --progress=plain
```

## Production Deployment

### Prerequisites
1. Server with Docker installed (or Podman)
2. Domain name configured in your `.env` file.
3. At least 2GB free disk space

### Steps
1. Clone repository on server
2. Configure `.env` with production values
3. Run: `./deploy.sh`

### Health Monitoring
```bash
# Check service health
curl https://your-domain-name/api/health

# Monitor logs
<compose_command> logs -f backend

# Check system resources
<container_tool> stats
```

## Performance Metrics

- **Build Time:** ~60 seconds
- **Startup Time:** ~10 seconds
- **Memory Usage:** 500-700 MB
- **Disk Space:** ~400 MB

## Security

- Non-root container users
- Environment variable isolation
- Security headers configured
- CORS protection enabled
- Input validation middleware
- SSL/TLS support (via Nginx)

## Database

### Backup
```bash
<compose_command> exec postgres pg_dump -U postgres hebrew_ai_db > backup.sql
```

### Restore
```bash
<compose_command> exec -T postgres psql -U postgres hebrew_ai_db < backup.sql
```

### Access Database
```bash
<compose_command> exec postgres psql -U postgres -d hebrew_ai_db
```

## External Nginx Configuration

If you have system-wide Nginx, configure upstream servers:

```nginx
upstream backend {
    server localhost:3001;
}

server {
    listen 80;
    server_name your-domain-name;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then reload: `sudo systemctl reload nginx`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test: `node tests/run-all-tests.js`
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature/your-feature`
6. Submit a pull request

## Testing
- All tests must pass before PR merge
- Run: `node tests/run-all-tests.js`
- Full deployment test: `./tests/test-deployment-podman.sh` (Requires Podman and podman-compose)

## License

MIT License - see LICENSE file for details

## Support

### Common Issues

**Q: How do I use external Nginx?**
A: Run `node tests/nginx-detection.test.js` - system auto-detects and configures

**Q: Can I scale the backend?**
A: Yes: `<compose_command> up -d --scale backend=3`

**Q: How do I view logs?**
A: Run: `<compose_command> logs -f [service]`

**Q: How do I backup the database?**
A: Run: `<compose_command> exec postgres pg_dump -U postgres hebrew_ai_db > backup.sql`

## Contact

- Report issues: [GitHub Issues](https://github.com/your-username/hebrew-ai-2025/issues)
- Discussions: [GitHub Discussions](https://github.com/your-username/hebrew-ai-2025/discussions)

## Acknowledgments

- Express.js - Web framework
- PostgreSQL - Database
- Redis - Caching
- Nginx - Web server
- Docker - Containerization
- deSEC.io - Free DNS hosting
- Let's Encrypt - Free SSL/TLS Certificates