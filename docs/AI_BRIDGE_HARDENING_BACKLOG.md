# AI Bridge Hardening Backlog

Status: Proposed  
Scope: orchestrator, runtime isolation, reliability, governance, CI/CD hardening

## 1) Runtime Isolation

| ID | Task | Owner Agent | SP | Dependencies | DoD |
|---|---|---|---:|---|---|
| RI-01 | Add rootless sandbox runner for agent execution in `host_bridge` | CodexAgent | 8 | - | Untrusted task runs as non-root in isolated runtime |
| RI-02 | Add seccomp `default-deny` + syscall allowlist profile | ReviewerAgent + CodexAgent | 5 | RI-01 | Container profile loaded and enforced in tests |
| RI-03 | Add AppArmor profile for process/filesystem confinement | ReviewerAgent + CodexAgent | 5 | RI-01 | AppArmor policy applied to sandboxed runs |
| RI-04 | Enforce cgroup limits (CPU/memory/pids/IO) per task | CodexAgent | 5 | RI-01 | Limits configurable and verified by tests |
| RI-05 | Add network namespace isolation and egress deny-by-default | CodexAgent | 8 | RI-01 | No outbound network unless explicit allowlist |
| RI-06 | Implement ephemeral lifecycle: create->run->collect->destroy | CodexAgent | 5 | RI-01 | Sandbox artifacts collected and sandbox removed |
| RI-07 | Timeout kill-switch + orphan sandbox cleanup sweeper | CodexAgent + TesterAgent | 3 | RI-06 | Timed-out run is terminated; cleanup job removes leftovers |

## 2) Observability & Monitoring

| ID | Task | Owner Agent | SP | Dependencies | DoD |
|---|---|---|---:|---|---|
| OM-01 | Integrate OpenTelemetry SDK in orchestrator/router/host bridge | CodexAgent | 8 | - | Spans emitted from critical runtime components |
| OM-02 | Propagate correlation IDs (`task_id`,`trace_id`,`agent_id`) end-to-end | CodexAgent | 5 | OM-01 | IDs present in logs, traces, queue payload |
| OM-03 | Standardize structured JSON logs with shared schema | CodexAgent + ReviewerAgent | 3 | OM-02 | Log schema documented and validated in tests |
| OM-04 | Add spans: `security_gate`,`model_select`,`route`,`execute`,`merge`,`retry` | CodexAgent | 3 | OM-01 | Span tree visible in trace backend |
| OM-05 | Add metrics: queue depth/retries/timeouts/success/failure/latency | CodexAgent + TesterAgent | 5 | OM-01 | Metrics endpoint exports required counters/histograms |
| OM-06 | Export telemetry to Loki/OTLP endpoints | CodexAgent + DocsAgent | 3 | OM-03, OM-04 | Production config supports OTLP + log shipping |

## 3) Queue & Execution Reliability

| ID | Task | Owner Agent | SP | Dependencies | DoD |
|---|---|---|---:|---|---|
| QR-01 | Introduce persistent task queue with status machine | CodexAgent | 8 | - | States: queued/running/retry/dlq/done implemented |
| QR-02 | Add retry policy: exponential backoff + jitter + max attempts | CodexAgent | 5 | QR-01 | Retry behavior deterministic and covered by tests |
| QR-03 | Add per-stage timeout + global SLA timeout orchestration | CodexAgent | 5 | QR-01 | Task times out predictably and escalates |
| QR-04 | Add DLQ and failure reason taxonomy | CodexAgent + ReviewerAgent | 3 | QR-01 | DLQ retains payload + normalized reason code |
| QR-05 | Failure escalation: auto-fix task, fallback route, operator alert hook | CodexAgent + DocsAgent | 5 | QR-02, QR-04 | Escalation path runs and emits alert event |

## 4) Secrets Management

| ID | Task | Owner Agent | SP | Dependencies | DoD |
|---|---|---|---:|---|---|
| SM-01 | Move API keys to secret backend (env-scope + mounts) | CodexAgent | 5 | - | Runtime reads secrets only from controlled store |
| SM-02 | Add redaction policy for logs/traces/events | ReviewerAgent + CodexAgent | 3 | OM-03 | No secret values appear in logs/traces |
| SM-03 | Add rotation workflow (versioned secrets + cutover) | PlannerAgent + CodexAgent | 5 | SM-01 | Rotation runbook and cutover script validated |
| SM-04 | Startup secret validation and fail-fast on missing/invalid | CodexAgent + TesterAgent | 3 | SM-01 | Startup fails with explicit diagnostics |

## 5) Supply Chain Security

| ID | Task | Owner Agent | SP | Dependencies | DoD |
|---|---|---|---:|---|---|
| SC-01 | Generate SBOM for backend/frontend/ai_bridge images | CodexAgent | 3 | - | SBOM artifacts attached in CI |
| SC-02 | Add image scanning in CI with fail-on-critical | ReviewerAgent + CodexAgent | 3 | SC-01 | CI blocks critical vulnerabilities |
| SC-03 | Pin/verify base images by digest and signature check | ReviewerAgent + CodexAgent | 5 | SC-02 | Build fails on invalid signature/digest mismatch |
| SC-04 | Dependency verification and artifact attestation | ReviewerAgent + CodexAgent | 5 | SC-01 | Provenance and verification reports published |

## 6) DB & Migration Reliability

| ID | Task | Owner Agent | SP | Dependencies | DoD |
|---|---|---|---:|---|---|
| DB-01 | Startup sequencing with DB ready + migration lock | CodexAgent | 3 | - | Backend start blocked until lock+readiness pass |
| DB-02 | Transactional migrations + rollback-aware workflow | CodexAgent + ReviewerAgent | 5 | DB-01 | Failed migration rolls back cleanly |
| DB-03 | CI pre-deploy migration dry-run step | TesterAgent + CodexAgent | 3 | DB-02 | CI fails on migration dry-run errors |
| DB-04 | Backup snapshot hook before risky migration sets | DocsAgent + CodexAgent | 3 | DB-02 | Snapshot hook documented and automated |

## 7) Rollback Strategy

| ID | Task | Owner Agent | SP | Dependencies | DoD |
|---|---|---|---:|---|---|
| RB-01 | Add post-deploy health gates | TesterAgent + CodexAgent | 3 | OM-05 | Gate blocks unhealthy rollout |
| RB-02 | Auto-rollback on failed startup or health degradation | CodexAgent | 5 | RB-01 | Failed rollout self-recovers to previous release |
| RB-03 | Persist release manifest + diagnostics bundle | DocsAgent + CodexAgent | 3 | RB-02 | Bundle includes versions, logs, health evidence |

## 8) AI Agent Governance

| ID | Task | Owner Agent | SP | Dependencies | DoD |
|---|---|---|---:|---|---|
| AG-01 | Capability-scoped permission model (`who can execute what`) | ReviewerAgent + CodexAgent | 8 | - | Authorization decision deterministic and test-covered |
| AG-02 | Policy check before route/execute | CodexAgent | 3 | AG-01 | Unauthorized task rejected before execution |
| AG-03 | Audit trail for authorize/deny/override | ReviewerAgent + CodexAgent | 3 | AG-01 | Every policy decision logged with correlation ID |
| AG-04 | Enforce `can_finalize=false` for untrusted external agents | ReviewerAgent + CodexAgent | 2 | AG-01 | External contributors cannot finalize result |

## 9) Frontend + CI/CD

| ID | Task | Owner Agent | SP | Dependencies | DoD |
|---|---|---|---:|---|---|
| FE-01 | Accessibility uplift (keyboard nav, semantics, focus states) | DocsAgent + TesterAgent | 5 | - | A11y checks pass and keyboard flows covered |
| FE-02 | React Query caching/invalidations/optimistic updates | CodexAgent | 5 | - | Reduced duplicate fetches and faster dashboard updates |
| CD-01 | Preview environment per PR | PlannerAgent + CodexAgent | 5 | - | PR gets isolated deploy URL + smoke checks |
| CD-02 | Deterministic builds via pinned toolchains/containers | ReviewerAgent + CodexAgent | 3 | - | Reproducible build hash policy in CI |

## AI Contributor Constraint

- `GeminiCLIAgent` and `MistralAgent` are draft contributors only.
- They may propose policies/templates/dashboards and test vectors.
- They are explicitly forbidden to finalize production decisions (`can_finalize=false`).

## Execution Order

1. RI -> OM -> QR -> SM (Critical path for R1)
2. RB in parallel with late R1 once OM+QR available
3. SC + DB as R2
4. AG + FE/CD as R3
5. Distributed/event-driven/multi-tenant as R4

## 10) API Telemetry Reliability & Error Taxonomy (Logs 1454)

Input snapshot: total=1454, success=1332, blocked=88, errors=34.

### Decomposition (Micro Tasks)

| ID | Task | Owner Agent | SP | Dependencies | DoD |
|---|---|---|---:|---|---|
| AP-01 | Add `/api/admin/logs/codes` endpoint with grouped status code distribution and top failing paths | CodexAgent | 3 | - | Endpoint returns code histogram + path/action slices |
| AP-02 | Add warning tiers in API summary (`warn`, `critical`) based on blocked/error ratio and p95 latency | CodexAgent + ReviewerAgent | 3 | AP-01 | Summary includes deterministic severity flags |
| AP-03 | Normalize auth telemetry reasons to strict enum (`invalid_password`,`user_not_found`,`locked`,`token_invalid`,`permission_denied`) | CodexAgent | 2 | - | No free-form reason drift in telemetry metadata |
| AP-04 | Add per-code SLO checks in CI smoke (`401`,`403`,`404`,`409`,`423`,`500`) | TesterAgent | 3 | AP-01 | CI artifact includes code-frequency sanity checks |
| AP-05 | Add blocked/error drilldown widgets in admin panel with trend + top codes | DocsAgent + CodexAgent | 3 | AP-01, AP-02 | Admin UI shows top blocked/error codes and endpoints |
| AP-06 | Add telemetry write-failure alerting metric (`telemetry_insert_failures_total`) | CodexAgent | 2 | - | Failures visible in metrics/logs and alertable |
| AP-07 | Add runbook section: interpretation of blocked vs error and operator actions per status code | DocsAgent | 2 | AP-02 | Runbook includes response matrix by HTTP code |
| AP-08 | Add regression tests for outcome classifier (`success/blocked/error`) including 423 lock case | TesterAgent | 2 | - | Tests protect classifier behavior |
| AP-09 | Add policy review for over-blocking paths (auth lock threshold, forbidden checks) | ReviewerAgent | 2 | AP-03 | Review report with approved threshold policy |
| AP-10 | Add orchestrator-side incident hook when API error ratio exceeds threshold | PlannerAgent + CodexAgent | 3 | AP-02, AP-06 | Bridge receives incident task when threshold crossed |

### Encapsulation by AI Agents

- PlannerAgent:
  - Build rollout order AP-01 -> AP-03 -> AP-08 -> AP-02 -> AP-04/AP-05 -> AP-07 -> AP-10.
  - Define release gates for blocked/error ratio.
- CodexAgent:
  - Implement backend telemetry/query changes in existing routes/middleware.
  - Implement metrics and incident hooks without adding parallel duplicate modules.
- TesterAgent:
  - Add classifier + API summary tests and CI checks for code distribution regressions.
- ReviewerAgent:
  - Validate taxonomy consistency and over-blocking policy impact.
- DocsAgent:
  - Update admin/logs interpretation and runbook response matrix.
- GeminiCLIAgent:
  - Generate draft anomaly explanations from code histogram (non-final).
- MistralAgent:
  - Generate draft remediation suggestions for top failing paths (non-final).

### Decapsulation (Unified Ready Variant)

- One telemetry contract across middleware/routes/admin UI:
  - stable outcome classifier,
  - normalized reason codes,
  - grouped status-code analytics,
  - operator severity and response guidance.
- Single operational workflow:
  - detect (AP-02/AP-06) -> diagnose (AP-01/AP-05) -> act (AP-07/AP-09) -> prevent regression (AP-04/AP-08).
- No new parallel subsystem: only incremental changes to existing telemetry/logs modules and orchestrator hooks.
