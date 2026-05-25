# AI Bridge Session Memory Release Plan (Decapsulated)

## Unified Target State

A single orchestrator execution model where every agent receives reusable, scoped, temporary context with strict security redaction and freshness checks.

## R1 (Implement Now)

- SessionMemory core with in-memory backend and TTL.
- Envelope memory metadata fields.
- `memory_context` passed into agent execution.
- Write-back of `last_result` / `last_summary`.
- Redaction and max entry size policy.
- Core tests.

Release gate:
- All session memory tests pass.
- No sensitive values persist in memory entries.

## R2

- Agent-specific memory key conventions.
- Cross-agent context handoff optimization.

Release gate:
- Planner/Tester/Reviewer/Codex/Docs consume scoped memory in integration tests.

## R3

- Fingerprint-based stale cache invalidation.
- Change-driven recalc for dependency and config-sensitive caches.

Release gate:
- Cache miss enforced after file/lock/config changes.

## R4

- Redis backend for shared session memory in distributed workers.
- Queue retry/DLQ path reads previous context.

Release gate:
- Multiple workers share context with TTL correctness.

## Single Execution Flow

1. Orchestrator receives task with `session_id` and memory policy.
2. Memory lookup is done by scope + keys.
3. Agent executes with `memory_context`.
4. Result is redacted and stored in memory.
5. Invalidation policy decides if memory is still valid.
