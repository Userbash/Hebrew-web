# Hebrew AI 2025

A modern, production-ready Hebrew language learning platform with automated testing and deployment infrastructure.

## Quick Start

### Prerequisites
- Docker & Docker Compose (or Podman & podman-compose)
- Node.js 18+ (for testing)
- 2GB free disk space

### Deploy in 30 Seconds

```bash
# 1. Clone the repository
git clone https://github.com/your-username/hebrew-ai-2025.git
cd hebrew-ai-2025

# 2. Copy environment configuration
cp .env.example .env

# 3. Deploy
./deploy.sh
```

### Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:3001
- **Health Check:** http://localhost:3001/api/health

## Features

### Core Services
- **Backend API** - Node.js Express server with modern middleware
- **Frontend** - Static HTML/JavaScript web interface
- **PostgreSQL** - Persistent data storage
- **Redis** - Caching layer
- **Nginx** - Reverse proxy & load balancing

### Automated Testing
- Path and configuration verification
- Dockerfile syntax validation
- docker-compose configuration checking
- Backend API health checks
- Complete deployment testing with Podman/Docker

### Smart Deployment
- Automatic external Nginx detection
- Zero-manual configuration needed
- Health checks with automatic retry
- Graceful error handling and rollback

## Project Structure

```
hebrew-ai-2025/
├── backend/                 # Node.js API
│   ├── api/
│   │   ├── routes/         # API endpoints
│   │   ├── middleware/     # Express middleware
│   │   └── data/           # Data storage
│   ├── server.js           # Main server file
│   └── package.json
├── frontend/               # Web UI
│   ├── pages/             # HTML pages
│   ├── css/               # Stylesheets
│   └── js/                # Client-side scripts
├── tests/                 # Test suite
│   ├── run-all-tests.js
│   ├── nginx-detection.test.js
│   ├── backend-verification.test.js
│   └── test-deployment-podman.sh
├── docker-compose.yml     # Container orchestration
├── backend.Dockerfile
├── frontend.Dockerfile
├── nginx.conf
├── .env                   # Environment variables (create from .env.example)
└── README.md
```

## Configuration

### Environment Variables

Create `.env` from `.env.example`:

```bash
# Database
DB_USER=postgres
DB_PASSWORD=secure_password_here
DB_NAME=hebrew_ai_db
DB_PORT=5432

# Backend
BACKEND_PORT=3001
NODE_ENV=production

# Frontend
FRONTEND_PORT=3000

# Nginx
NGINX_PORT=80
NGINX_HTTPS_PORT=443

# External Nginx (auto-detected - leave empty if using internal Nginx)
EXTERNAL_NGINX=false
```

## Deployment Options

### Option 1: Standard Deployment (Recommended)
```bash
./deploy.sh
```
- Builds images
- Starts containers
- Runs health checks

### Option 2: With Testing
```bash
./deploy.sh
node tests/run-all-tests.js
```

### Option 3: External Nginx
If you have system-wide Nginx running:
```bash
node tests/nginx-detection.test.js
# System will auto-detect and configure appropriately
./deploy.sh
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login

### Users
- `GET /api/users/profile` - Get user profile

### Content
- `GET /api/lessons` - Get all lessons
- `GET /api/quizzes` - Get all quizzes
- `GET /api/dictionary/:word` - Search dictionary

### Progress
- `GET /api/progress/:userId` - Get user progress

### Health
- `GET /api/health` - Service health check

## Development

### Running Tests
```bash
# Run all verification tests
node tests/run-all-tests.js

# Test specific components
node tests/nginx-detection.test.js
node tests/backend-verification.test.js
node tests/docker-compose-validator.test.js

# Full Podman deployment test
./tests/test-deployment-podman.sh
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Manage Services
```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart specific service
docker-compose restart backend

# View service status
docker-compose ps

# Resource usage
docker stats
```

## Troubleshooting

### Port Already in Use
```bash
# Check which process is using the port
ss -tuln | grep :3000

# Change port in .env and restart
docker-compose down
docker-compose up -d
```

### Backend Connection Error
```bash
# Check logs
docker-compose logs backend

# Verify health
curl http://localhost:3001/api/health

# Restart service
docker-compose restart backend
```

### Build Issues
```bash
# Force rebuild
docker-compose build --no-cache

# Check build logs
docker-compose build --progress=plain
```

## Production Deployment

### Prerequisites
1. Server with Docker installed
2. SSL certificates (optional, for HTTPS)
3. Domain name configured
4. At least 2GB free disk space

### Steps
1. Clone repository on server
2. Configure `.env` with production values
3. Run: `./deploy.sh`
4. Configure Nginx/SSL (if needed) - see NGINX_CONFIG.md

### Health Monitoring
```bash
# Check service health
curl https://your-domain.com/api/health

# Monitor logs
docker-compose logs -f backend

# Check system resources
docker stats
```

## Performance Metrics

- **Build Time:** ~75 seconds
- **Startup Time:** ~15 seconds
- **Memory Usage:** 600-800 MB
- **Disk Space:** ~500 MB

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
docker-compose exec postgres pg_dump -U postgres hebrew_ai_db > backup.sql
```

### Restore
```bash
docker-compose exec -T postgres psql -U postgres hebrew_ai_db < backup.sql
```

### Access Database
```bash
docker-compose exec postgres psql -U postgres -d hebrew_ai_db
```

## External Nginx Configuration

If you have system-wide Nginx, configure upstream servers:

```nginx
upstream backend {
    server localhost:3001;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
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
- Full deployment test: `./tests/test-deployment-podman.sh`

## License

MIT License - see LICENSE file for details

## Support

### Common Issues

**Q: How do I use external Nginx?**
A: Run `node tests/nginx-detection.test.js` - system auto-detects and configures

**Q: Can I scale the backend?**
A: Yes: `docker-compose up -d --scale backend=3`

**Q: How do I view logs?**
A: Run: `docker-compose logs -f [service]`

**Q: How do I backup the database?**
A: Run: `docker-compose exec postgres pg_dump -U postgres hebrew_ai_db > backup.sql`

## Contact

- Report issues: [GitHub Issues](https://github.com/your-username/hebrew-ai-2025/issues)
- Discussions: [GitHub Discussions](https://github.com/your-username/hebrew-ai-2025/discussions)

## Acknowledgments

- Express.js - Web framework
- PostgreSQL - Database
- Redis - Caching
- Nginx - Web server
- Docker - Containerization
