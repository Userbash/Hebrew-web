# Multi-stage build for Frontend (Static HTML/JavaScript)

# ============================================================================
# STAGE 1: RUNTIME (Using Nginx for production)
# ============================================================================
FROM nginx:alpine

LABEL maintainer="Frontend Team"
LABEL version="1.0"
LABEL description="Static HTML/JavaScript Frontend Runtime"

ARG NODE_ENV=production
ARG REACT_APP_API_URL=http://localhost:3001

# Install curl for healthcheck
RUN apk add --no-cache curl dumb-init

# Create non-root user for nginx
RUN addgroup -g 1001 web && \
    adduser -S web -u 1001 -G web

# Create directories
RUN mkdir -p /var/cache/nginx /var/log/nginx /app/uploads && \
    chown -R web:web /var/cache/nginx /var/log/nginx /app

WORKDIR /usr/share/nginx/html

# Copy static files
COPY pages ./pages
COPY css ./css
COPY js ./js

# Copy nginx configuration (create a simple default config)
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 3000;
    server_name localhost;
    root /usr/share/nginx/html;

    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss;
    gzip_vary on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Caching
    expires 30d;
    add_header Cache-Control "public, immutable";

    location / {
        try_files $uri $uri/ /pages/index.html;
        expires 1h;
        add_header Cache-Control "public";
    }

    location ~* \.(js|css)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location ~* \.(jpg|jpeg|png|gif|ico|woff|woff2)$ {
        expires 30d;
    }

    location /api/ {
        proxy_pass http://backend:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }
    location ~ /\.env {
        deny all;
    }
}
EOF

# Create health check script
RUN cat > /healthcheck.sh << 'EOF'
#!/bin/sh
curl -f http://localhost:3000/ || exit 1
EOF
RUN chmod +x /healthcheck.sh

# Set proper permissions
RUN chown -R web:web /usr/share/nginx/html

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --retries=5 --start-period=30s \
    CMD /healthcheck.sh

# Use dumb-init to handle signals
ENTRYPOINT ["/sbin/dumb-init", "--"]

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
