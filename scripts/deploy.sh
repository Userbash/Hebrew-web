#!/bin/bash

# Hebrew AI 2025 - Simple Deployment Script
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Hebrew AI 2025 - Deploy${NC}"
echo -e "${BLUE}================================${NC}\n"

CONTAINER_TOOL=""
COMPOSE_CMD=""

# Detect Podman
if command -v podman &> /dev/null && command -v podman-compose &> /dev/null; then
    CONTAINER_TOOL="Podman"
    COMPOSE_CMD="podman-compose"
    echo -e "${GREEN}✓ Podman and podman-compose available${NC}"
else
    echo -e "${RED}✗ Podman and podman-compose NOT found.${NC}"
    echo -e "${RED}Please install Podman and podman-compose to proceed.${NC}"
    exit 1
fi

fi

echo -e "${BLUE}Using ${CONTAINER_TOOL} for deployment.${NC}\n"

# Check .env
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${BLUE}! Configure .env and run again${NC}"
    exit 1
fi
echo -e "${GREEN}✓ .env configured${NC}\n"

# Deploy
echo "Deploying services..."
$COMPOSE_CMD down 2>/dev/null || true
$COMPOSE_CMD build --quiet || exit 1
$COMPOSE_CMD up -d || exit 1
echo -e "${GREEN}✓ Services started${NC}\n"

# Wait for backend
echo "Waiting for backend..."
for i in {1..30}; do
    if curl -sf http://localhost:3001/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend healthy${NC}\n"
        break
    fi
    sleep 1
done

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  ✓ Deployment Complete${NC}"
echo -e "${GREEN}================================${NC}\n"
echo "Frontend:     http://localhost:3000"
echo "API:          http://localhost:3001"
echo "Health:       http://localhost:3001/api/health"
echo ""
echo "Commands:"
echo "  ${COMPOSE_CMD} logs -f              # View logs"
echo "  ${COMPOSE_CMD} down                 # Stop services"
echo "  ${CONTAINER_TOOL} stats                        # Resource usage"
