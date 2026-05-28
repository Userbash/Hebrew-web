FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY ai_bridge/requirements-ai.txt /app/ai_bridge/requirements-ai.txt
RUN pip install --no-cache-dir -r /app/ai_bridge/requirements-ai.txt

COPY ai_bridge /app/ai_bridge

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["python", "-m", "ai_bridge.scripts.orchestrator_daemon"]
