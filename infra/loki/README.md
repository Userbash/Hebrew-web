# Loki logging pipeline

This project can ship container logs to Loki through Promtail and view them in Grafana.

## What is configured

- Docker `json-file` log rotation in `docker-compose.yml` with `max-size` and `max-file` limits.
- Stable container labels: `com.hebrew.service`, `com.hebrew.component`, `com.hebrew.log_pipeline`.
- Loki filesystem storage with retention in `infra/loki/loki-config.yaml`.
- Promtail Docker service discovery in `infra/loki/promtail-config.yaml`.
- Grafana Loki datasource provisioning in `infra/grafana/provisioning/datasources/loki.yaml`.
- JSON access logs for Traefik and nginx frontend.

## Useful LogQL queries

```logql
{service="backend"}
{service="frontend"}
{service="traefik"}
{component="api"} |= "error"
sum by (service) (rate({log_pipeline="loki"}[5m]))
```

## Docker Compose

Start the stack with a Docker Compose provider:

```bash
docker compose up -d --build
```

Open Grafana at `http://localhost:3000` and use the provisioned `Loki` datasource.

## Podman notes

The checked-in Promtail config uses Docker socket discovery because Traefik and Compose labels are Docker-oriented. For Podman rootless deployments, use one of these approaches:

- expose a Docker-compatible Podman socket and point Promtail to it;
- or switch Promtail to journald scraping and add service labels through systemd unit metadata.

When building images with Podman and relying on Dockerfile `HEALTHCHECK`, use Docker image format:

```bash
podman build --format docker -t hebrew-ai-backend:local -f backend/Dockerfile .
podman build --format docker -t hebrew-ai-frontend:local -f frontend-react/Dockerfile frontend-react
```
