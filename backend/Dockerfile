FROM node:20-alpine AS builder
WORKDIR /app

COPY backend/package*.json ./
RUN npm ci

COPY backend/ ./
RUN npm run build

FROM node:20-alpine
WORKDIR /app

RUN apk add --no-cache curl

COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/public ./public
COPY --from=builder /app/database ./database

ENV NODE_ENV=production
EXPOSE 3001

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=8 \
  CMD curl -fsS http://127.0.0.1:3001/api/health || exit 1

CMD ["node", "dist/server.js"]
