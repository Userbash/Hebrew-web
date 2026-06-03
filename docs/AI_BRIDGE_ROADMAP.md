# AI Bridge Hardening & Memory Roadmap

This document tracks the execution phases and backlogs for the AI Bridge orchestration layer.

## 1. Release Waves (R1-R4)

### R1: Critical Hardening
- **Isolation**: Rootless sandbox runner, seccomp/AppArmor profiles, cgroup limits.
- **Observability**: OpenTelemetry integration, end-to-end correlation IDs, standardized JSON logs.
- **Reliability**: Persistent task queue, exponential backoff retries, Dead Letter Queue (DLQ).
- **Secrets**: API keys moved to secure backend, redaction policy for logs.

### R2: Secure Delivery
- **Supply Chain**: SBOM generation, image scanning in CI, pinned base images.
- **DB Stability**: Transactional migrations, dry-run validation, backup snapshot hooks.
- **Memory**: Agent-specific memory keys, cross-agent context handoff.

### R3: Governance & Scale
- **Policies**: Capability-scoped permissions, audit trails for policy decisions.
- **Performance**: React Query caching, optimized dashboard data layer.
- **Memory**: Fingerprint-based stale cache invalidation.

### R4: Long-Term Architecture
- **Infrastructure**: Async/event-driven execution bus, distributed workers (Redis backend).
- **Isolation**: Multi-tenant isolation and advanced policy engine.

## 2. Memory Upgrade Tasks

| ID | Task | Agent | DoD |
|---|---|---|---|
| MU-01 | Implement pgvector storage | CodexAgent | pgvector query in `persistent_memory.py` |
| MU-04 | Add cross-encoder reranking | CodexAgent | Cross-encoder model reranks top-K results |
| MU-16 | Implement memory decay | CodexAgent | Time-decay formula implemented |
| MU-28 | Implement deduplication | CodexAgent | Cosine similarity > 0.98 merged |
| MU-35 | Prevent secret leaks | ReviewerAgent | Regex/Entropy secret scanner |

## 3. Session Memory Specification

Temporary execution memory for a single runtime session to reuse context (project tree, dependency scan, test results) and avoid repeated expensive scans.

### Security Controls
- Redaction before write.
- Denylist for sensitive keys (`api_key`, `token`, `password`).
- TTL-aware entries with invalidation on repo fingerprint mismatch.

## 4. API Telemetry & Error Taxonomy
- Group status code distribution and top failing paths.
- Normalize auth telemetry reasons to strict enums.
- Implement per-code SLO checks in CI smoke tests.
