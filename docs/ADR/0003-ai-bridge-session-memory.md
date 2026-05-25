# ADR-0003: AI Bridge Session Memory

- Status: Proposed
- Date: 2026-05-25
- Supersedes: none

## Context

Agent workflows repeatedly recalculate identical project and validation context in a single orchestration session. This increases latency and noise.

## Decision

Introduce Session Memory with scoped temporary cache:

- `session`, `task`, `agent`, `capability`
- TTL-aware entries
- Security redaction before write
- Invalidation support by key prefix and repository fingerprint

R1 backend is in-memory. Redis-backed backend is deferred to R4.

## Consequences

### Positive

- Lower repeated execution cost.
- Faster handoff between agents.
- Better routing consistency through reusable context.

### Tradeoffs

- Potential stale cache risk without strict invalidation.
- Additional policy logic for secure memory writes.

## Implementation

- `ai_bridge/core/session_memory.py`
- `ai_bridge/core/memory_backend.py`
- `ai_bridge/core/memory_policy.py`
- `ai_bridge/core/memory_invalidator.py`
