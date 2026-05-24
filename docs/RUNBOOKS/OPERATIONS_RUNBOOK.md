# Operations Runbook

## Scope

Operational procedures for backend, frontend, and observability stack in containerized environments.

## Standard Startup

1. Validate environment variables (`.env` against `.env.example`).
2. Build and start services:
   - `bash scripts/build_abstracted.sh`
   - `bash scripts/start_manual.sh`
3. Confirm health:
   - Backend: `GET /api/health`
   - Frontend: root page health check
   - Infra: Loki/Grafana readiness endpoints

## Standard Shutdown

- Use service-specific stop scripts when available.
- Ensure no in-progress migrations or data backfills before shutdown.

## Routine Checks

- Container health status (`healthy` expected)
- Error-rate spikes in logs
- Admin API latency trends
- DB connectivity and lock contention metrics

## Change Deployment Procedure

1. Review changelog and migration plan.
2. Run tests:
   - `npm test`
   - backend lint/build
   - frontend lint/build
   - `python3 -m pytest ai_bridge/tests`
3. Deploy using approved compose flow.
4. Run post-deploy smoke checks.
5. Record release manifest and rollback notes.

