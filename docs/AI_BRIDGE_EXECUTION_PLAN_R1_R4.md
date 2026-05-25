# AI Bridge Execution Plan (R1-R4)

Status: Proposed  
Input source: orchestrator hardening decomposition  
Backlog reference: `docs/AI_BRIDGE_HARDENING_BACKLOG.md`

## Encapsulation By Agent

### PlannerAgent
- Build dependency graph for all backlog IDs.
- Maintain sprint capacity, priority lanes, and risk matrix.
- Output: milestone plan, critical path control, blocked-task registry.

### CodexAgent
- Implement runtime code and infrastructure glue:
  - sandbox runner and isolation controls,
  - queue, retry, timeout, DLQ flows,
  - telemetry instrumentation and secret integration hooks,
  - rollout/rollback mechanics.

### TesterAgent
- Deliver unit/integration/e2e and chaos suites:
  - timeout storm,
  - queue backlog pressure,
  - crash/recovery and rollback validation.

### ReviewerAgent
- Own governance, security model quality, least-privilege controls:
  - seccomp/AppArmor review,
  - capability authorization model,
  - supply-chain and policy gate quality checks.

### DocsAgent
- Provide runbooks, architecture diagrams, release evidence pack:
  - incident response,
  - rollback and secret rotation,
  - deployment/operator procedures.

### GeminiCLIAgent / MistralAgent (external contributors)
- Draft-only support:
  - policy templates,
  - hardening snippets,
  - dashboard/query starters.
- Constraint: no finalization authority (`can_finalize=false`).

## Decapsulation Into Release Package

## R1: Critical Hardening (2-3 sprints)
- Scope: RI-01..RI-07, OM-01..OM-06, QR-01..QR-05, SM-01..SM-04, RB-01.
- Acceptance:
  - Untrusted workloads run isolated in rootless sandbox.
  - Correlated traces/logs available end-to-end.
  - Queue + retry + timeout + DLQ execution stable.
  - Secret leakage blocked by redaction policy.

## R2: Secure Delivery (1-2 sprints)
- Scope: SC-01..SC-04, DB-01..DB-04, RB-02..RB-03.
- Acceptance:
  - CI enforces SBOM, scanning, digest/signature checks.
  - Migrations are dry-run validated and rollback-aware.
  - Failed rollout can auto-rollback with diagnostics bundle.

## R3: Governance & Scale Preparation (2 sprints)
- Scope: AG-01..AG-04, FE-01, FE-02, CD-01, CD-02.
- Acceptance:
  - Capability policy is enforced before execution.
  - Audit logs cover authorize/deny/override events.
  - Dashboard data layer is cache-aware and responsive.
  - PR preview and reproducible builds are active in CI/CD.

## R4: Long-Term Architecture
- Scope:
  - async/event-driven execution bus,
  - distributed workers,
  - multi-tenant isolation and policy engine.
- Acceptance:
  - Horizontal scaling path validated by load tests.
  - Orchestrator is no longer a single bottleneck path.

## Monday Start Order (First 5 Execution Tasks)

1. Introduce execution envelope fields: `correlation_id`, `timeout_policy`, `retry_policy`, `capability_scope`.
2. Add sandbox runner integration in `host_bridge`.
3. Add persistent queue core and retry executor with DLQ.
4. Enable OTel + structured logging in orchestrator flow.
5. Wire secret backend + redaction + startup validation.

## Success KPIs

- 99th percentile task latency (per capability and per agent).
- Retry success ratio and DLQ rate.
- Timeout rate and rollback success ratio.
- Trace completeness for critical execution path.
- Secret redaction violation count (must remain zero).
