FROM python:3.12-alpine
WORKDIR /app
RUN apk add --no-cache curl bash tini

RUN mkdir -p /app/public/uploads/avatars
COPY backend/init-ai-bridge.sh ./init-ai-bridge.sh
RUN chmod +x ./init-ai-bridge.sh

# Настройка путей для AI Bridge
COPY ai_bridge ./ai_bridge
ENV PYTHONPATH=/app:/app/ai_bridge
RUN mkdir -p /app/memory_store/memories /app/memory_store/commands && \
    chmod -R 777 /app/memory_store

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["./init-ai-bridge.sh"]
