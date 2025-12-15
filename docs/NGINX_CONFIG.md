# Nginx Configuration Guide

For production deployments with external Nginx reverse proxy.

## Setup External Nginx

### 1. Configure Upstream Servers

Create `/etc/nginx/conf.d/hebrew-ai-upstream.conf`:

```nginx
upstream backend {
    server localhost:3001;
    keepalive 32;
}

upstream frontend {
    server localhost:3000;
    keepalive 32;
}
```

### 2. Configure Server Block

Create `/etc/nginx/sites-available/hebrew-ai`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static Files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        proxy_pass http://frontend;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Enable Configuration

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/hebrew-ai /etc/nginx/sites-enabled/hebrew-ai

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## SSL Certificate with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## Using Internal Nginx

The application includes Nginx. Configure in `docker-compose.yml` port `80` and `443`.

## Troubleshooting

### 502 Bad Gateway
- Check backend is running: `docker-compose ps`
- Check logs: `docker-compose logs backend`

### SSL Certificate Issues
- Verify path: `sudo certbot certificates`
- Test SSL: `sudo openssl s_client -connect localhost:443`

### High Latency
- Check timeouts in Nginx config
- Monitor: `docker stats`
