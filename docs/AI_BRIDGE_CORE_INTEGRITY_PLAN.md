# AI Bridge Core Integrity Plan

## Micro Tasks (Decomposition)

1. Add system-level integrity test module: `ai_bridge/tests/test_core_integrity.py`.
2. Validate memory fields in execution model.
3. Validate SessionMemory API contract (`set/get/delete/clear_session`).
4. Validate TTL expiry behavior.
5. Validate secret redaction before memory persistence.
6. Validate agent API compatibility (`memory_context` support).
7. Add runtime self-check command module: `ai_bridge/core/core_healthcheck.py`.
8. Validate orchestrator wiring, registry, host bridge, container provider and policy config.

## Encapsulation By Agent

- PlannerAgent:
  - Maintain rollout order and dependencies for integrity checks.
  - Define acceptance gates for R1 and R2.

- CodexAgent:
  - Implement test module and healthcheck runtime module.
  - Ensure API compatibility layer in SessionMemory.

- TesterAgent:
  - Execute targeted and full test runs.
  - Report regressions and runtime readiness failures.

- ReviewerAgent:
  - Verify security assertions (redaction, no secret leakage).
  - Review integrity checks for false positives/coverage gaps.

- DocsAgent:
  - Document commands and interpretation of results.
  - Keep operational checklist updated.

- GeminiCLIAgent / MistralAgent:
  - Draft only: suggest additional checks and failure taxonomies.
  - No finalize rights.

## Decapsulation (Unified Ready Variant)

R1 (now):
- `test_core_integrity.py` + `core_healthcheck.py` + SessionMemory compatibility wrappers.
- Acceptance: targeted integrity test green, full ai_bridge test suite green.

R2:
- Extend healthcheck with deeper orchestrator flow probes and queue/memory invalidation checks.

R3:
- Add distributed backend readiness checks for Redis and worker topology.

R4:
- Production hardening checks for policy engine and multi-tenant isolation.
