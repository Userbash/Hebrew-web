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
    g++

WORKDIR /build

# Copy package files
COPY backend/package*.json ./

# Install dependencies with production optimizations
RUN npm ci --only=production && \
    npm cache clean --force

# ============================================================================
# STAGE 2: SECURITY SCANNER
# ============================================================================
FROM node:20-alpine AS security-scanner

WORKDIR /scan

COPY --from=builder /build/node_modules ./node_modules
COPY backend/package*.json ./

# Run security audit
RUN npm audit --audit-level=moderate && \
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
    socat \
    jq \
    openssl \
    coreutils \
    tar # tar for backup function

# Create non-root user
RUN addgroup -g 1001 nodejs && \
    adduser -S nodejs -u 1001 -G nodejs
WORKDIR /app

# Create necessary directories and set permissions as root
RUN mkdir -p /app/uploads /var/log/app /etc/letsencrypt /etc/letsencrypt/backup && \
    chown -R nodejs:nodejs /app /var/log/app /etc/letsencrypt && \
    chmod -R 700 /etc/letsencrypt

# Copy node_modules from builder stage
COPY --from=builder --chown=nodejs:nodejs /build/node_modules ./node_modules

# Copy application code
COPY --chown=nodejs:nodejs ./backend .

# Copy and make entrypoint script executable
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

# Set environment variables
ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=2048" \
    LOG_LEVEL=info \
    PORT=3001

# Set the entrypoint to the executable script
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
