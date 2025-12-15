# Multi-stage build for Node.js Backend

# ============================================================================
# STAGE 1: BUILDER
# ============================================================================
FROM node:20-alpine AS builder

LABEL maintainer="Backend Team"
LABEL version="1.0"
LABEL description="Node.js Backend API Builder"

# Install build dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    cairo-dev \
    jpeg-dev \
    pango-dev \
    giflib-dev

WORKDIR /build

# Copy package files
COPY package*.json ./

# Install dependencies with production optimizations
RUN npm ci --only=production && \
    npm cache clean --force

# ============================================================================
# STAGE 2: SECURITY SCANNER
# ============================================================================
FROM node:20-alpine AS security-scanner

WORKDIR /scan

COPY --from=builder /build/node_modules ./node_modules
COPY package*.json ./

# Run security audit
RUN npm audit --audit-level=moderate || true && \
    npm ls 2>/dev/null || true

# ============================================================================
# STAGE 3: RUNTIME
# ============================================================================
FROM node:20-alpine

LABEL maintainer="Backend Team"
LABEL version="1.0"
LABEL description="Node.js Backend API Runtime"

# Install runtime dependencies only
RUN apk add --no-cache \
    curl \
    dumb-init \
    tini \
    ca-certificates \
    bash \
    socat
    
# Install acme.sh
RUN curl https://get.acme.sh | sh

# Create non-root user
RUN addgroup -g 1001 nodejs && \
    adduser -S nodejs -u 1001 -G nodejs

WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/uploads /var/log/app && \
    chown -R nodejs:nodejs /app /var/log/app

# Copy node_modules from builder stage
COPY --from=builder --chown=nodejs:nodejs /build/node_modules ./node_modules

# Copy application code
COPY --chown=nodejs:nodejs . .

# Create health check script
RUN cat > /app/healthcheck.js << 'EOF'
const http = require('http');

const options = {
  hostname: 'localhost',
  port: process.env.PORT || 3001,
  path: '/api/health',
  method: 'GET',
  timeout: 5000
};

const req = http.request(options, (res) => {
  if (res.statusCode === 200) {
    process.exit(0);
  } else {
    process.exit(1);
  }
});

req.on('error', () => {
  process.exit(1);
});

req.end();
EOF

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=20s \
    CMD node /app/healthcheck.js

# Set environment variables
ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=2048" \
    LOG_LEVEL=info \
    PORT=3001
