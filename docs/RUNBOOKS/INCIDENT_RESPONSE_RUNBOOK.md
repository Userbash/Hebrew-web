# Incident Response Runbook

## Severity Model

- `SEV-1`: full outage or critical security incident
- `SEV-2`: major degradation with user impact
- `SEV-3`: partial degradation or non-critical component failure

## Initial Response Checklist

1. Open incident record with timestamp and owner.
2. Classify severity and impacted scope.
3. Freeze non-essential deployments.
4. Capture evidence:
   - affected endpoints
   - logs (Loki)
   - metrics (Grafana)
   - recent commits/releases

## Diagnostic Workflow

1. Verify service health endpoints.
2. Identify first failing component (edge, backend, DB, Redis, frontend).
3. Correlate telemetry and audit signals.
4. Validate whether issue aligns with recent schema/API/infra changes.

## Mitigation Strategy

- Prefer reversible mitigations first.
- If migration-related, follow `docs/DB_MIGRATION_PLAYBOOK.md`.
- If auth/RBAC related, validate policy changes against `docs/RBAC_MATRIX.md`.
- Rollback to last known healthy release if needed.

## Communication

- Provide updates every 15 minutes for SEV-1/SEV-2.
- Include: current status, mitigation step, ETA, risk.

## Closure

1. Confirm functional and operational recovery.
2. Publish postmortem with root cause and corrective actions.
3. Add follow-up tasks and changelog/security log entries as applicable.

