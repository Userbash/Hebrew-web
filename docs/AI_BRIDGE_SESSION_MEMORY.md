# AI Bridge Session Memory

## Goal

Provide temporary execution memory for a single runtime session so agents can reuse context and avoid repeated expensive scans.

## Scopes

- `session`
- `task`
- `agent`
- `capability`

## Stored Data Types

- `project_tree`
- `dependency_scan`
- `test_result`
- `security_findings`
- `agent_notes`
- `routing_decision`
- `command_result`
- `deployment_context`

## Security Controls

- Redaction before write.
- Denylist for sensitive keys (`api_key`, `token`, `password`, etc).
- Max entry size guard.
- Memory is temporary and can be cleared per session.

## Execution Envelope Fields

- `session_id`
- `memory_scope`
- `memory_keys`
- `memory_ttl_sec`
- `cache_policy`
- `repo_fingerprint`

## R1 Implementation

- In-memory backend (`dict`) with TTL.
- `SessionMemory.get/set/delete/invalidate/clear_session/list_keys`.
- Orchestrator loads `memory_context` before `agent.run()`.
- Orchestrator writes `last_result` and `last_summary` after execution.
