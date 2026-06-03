# Operational Runbooks

## 1. Startup & Deployment

### Standard Startup
1. Validate environment variables against `.env.example`.
2. Build services: `bash scripts/build_abstracted.sh`.
3. Start services: `bash scripts/start_manual.sh`.
4. Confirm health: `GET /api/health`.

### Deployment Procedure
1. Review changelog and migration plan.
2. Run full test suite: `npm test` and `pytest`.
3. Deploy using approved compose flow.
4. Record release manifest and rollback notes.

## 2. Incident Response

### Severity Model
- **SEV-1**: Full outage or critical security incident.
- **SEV-2**: Major degradation with user impact.
- **SEV-3**: Partial degradation or non-critical failure.

### Initial Response
1. Open incident record.
2. Classify severity.
3. Freeze deployments.
4. Correlate Loki logs and Grafana metrics.

### Mitigation & Recovery
- Prefer reversible mitigations.
- For DB issues, follow `docs/GOVERNANCE.md` migration rules.
- For RBAC issues, validate against role matrix.
- Rollback to last known healthy release if needed.

## 3. Routine Checks
- Container health status.
- Error-rate spikes in logs.
- Admin API latency trends.
- DB connectivity and lock contention.
