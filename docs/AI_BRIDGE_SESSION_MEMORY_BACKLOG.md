# AI Bridge Session Memory Backlog

Status: Proposed

## Epic SM-1: Core Session Memory (R1)

| ID | Task | Owner | SP | Depends On | DoD |
|---|---|---|---:|---|---|
| R1-SM-01 | Implement `SessionMemory` core (`get/set/delete/invalidate/clear/list`) | CodexAgent | 5 | - | API works with unit tests |
| R1-SM-02 | Add execution envelope fields for memory metadata | CodexAgent | 3 | R1-SM-01 | Task and envelope carry session memory fields |
| R1-SM-03 | Pass `memory_context` into `BaseAgent.run(...)` | CodexAgent | 3 | R1-SM-02 | Agents receive scoped cache context |
| R1-SM-04 | Add redaction + max size policy before write | ReviewerAgent + CodexAgent | 3 | R1-SM-01 | Sensitive values are masked; oversize blocked |
| R1-SM-05 | Add unit/integration tests | TesterAgent | 3 | R1-SM-01..04 | Tests green for ttl/redaction/context pass-through |

## Epic SM-2: Agent-Aware Context (R2)

| ID | Task | Owner | SP | Depends On | DoD |
|---|---|---|---:|---|---|
| R2-SM-01 | Planner memory keys: dependency graph, blocked tasks, risk matrix | PlannerAgent | 2 | R1-SM-03 | Planner reads/writes planned keys |
| R2-SM-02 | Codex memory keys: project tree, changed files, command outputs | CodexAgent | 3 | R1-SM-03 | Reused context observed in code tasks |
| R2-SM-03 | Tester memory keys: last tests, flaky list, coverage summary | TesterAgent | 3 | R1-SM-03 | Test reruns use cached context |
| R2-SM-04 | Reviewer memory keys: security findings, policy violations | ReviewerAgent | 3 | R1-SM-03 | Review step consumes cached security context |
| R2-SM-05 | Docs memory keys: ADR links, doc gaps, generated sections | DocsAgent | 2 | R1-SM-03 | Docs step reuses cached outline |
| R2-SM-06 | External draft memory for Gemini/Mistral (`can_finalize=false`) | ReviewerAgent | 2 | R1-SM-03 | Draft-only memory scope enforced |

## Epic SM-3: Invalidation and Freshness (R3)

| ID | Task | Owner | SP | Depends On | DoD |
|---|---|---|---:|---|---|
| R3-SM-01 | Add `repo_fingerprint` and lockfile/compose hashes | CodexAgent | 3 | R1-SM-02 | Fingerprint computed and stored |
| R3-SM-02 | Invalidate stale cache on fingerprint mismatch | CodexAgent | 3 | R3-SM-01 | Stale memory is not reused |
| R3-SM-03 | Add invalidation test scenarios (file/dependency/config changes) | TesterAgent | 3 | R3-SM-02 | Regression tests cover stale cache cases |

## Epic SM-4: Shared Memory Backend (R4)

| ID | Task | Owner | SP | Depends On | DoD |
|---|---|---|---:|---|---|
| R4-SM-01 | Introduce `MemoryBackend` abstraction | CodexAgent | 2 | R1-SM-01 | InMemory backend behind interface |
| R4-SM-02 | Implement `RedisMemoryBackend` with TTL support | CodexAgent | 5 | R4-SM-01 | Multi-worker shared memory works |
| R4-SM-03 | Wire queue/retry/DLQ flows to read session context | CodexAgent + TesterAgent | 3 | R4-SM-02 | Retry path can reuse prior task context |

## Encapsulated Ownership Map

- PlannerAgent: scope design, dependency graph memory, risk-state reuse.
- CodexAgent: runtime implementation and envelope integration.
- TesterAgent: reliability and regression verification.
- ReviewerAgent: policy/security gates, redaction governance.
- DocsAgent: operator docs and ADR traceability.
- GeminiCLIAgent/MistralAgent: draft snippets only, no finalization.
