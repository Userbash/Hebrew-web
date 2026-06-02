# AI Bridge

Reusable orchestration toolkit for agent-driven development workflows. It provides task decomposition, agent registration, capability routing, health checks, load balancing, feedback/retry loops, metrics, security guards, and protocol adapters for local and REST-based agents.

## Structure

```text
ai_bridge/
  core/          orchestration, routing, registry, metrics, security
  agents/        local and external agent abstractions
  protocols/     REST, websocket placeholder, local queue
  schemas/       JSON schemas for task, agent, result, metrics
  scripts/       small CLI entry points
  tests/         pytest coverage for core behavior
```

## Run Tests

From repository root:

```bash
python3 -m pytest ai_bridge/tests
```

Or:

```bash
python3 -m ai_bridge.scripts.run_tests
```

## Run Demo Orchestrator

```bash
python3 -m ai_bridge.scripts.run_orchestrator
```

The demo registers local planner, codex, tester, and reviewer agents and executes a plan -> code -> test -> review cycle.

## Register a New Agent

```python
from ai_bridge.core.agent_registry import AgentRegistry

registry = AgentRegistry()
registry.register(
    agent_id="docs-1",
    agent_type="docs",
    endpoint="local://docs-1",
    capabilities=["docs"],
)
```

Agent fields:
- `id`: stable unique agent id.
- `type`: `codex`, `reviewer`, `tester`, `planner`, `docs`, `external_ai`, or `custom`.
- `endpoint`: `local://...` or HTTP base URL.
- `capabilities`: routing capabilities such as `code`, `fix`, `review`, `security`, `test`, `docs`.

## Healthcheck Contract

Every remote agent should expose:

```http
GET /health
```

Response:

```json
{
  "agent_id": "reviewer-1",
  "status": "ready",
  "capabilities": ["review", "security"],
  "active_tasks": 0,
  "queue_depth": 0,
  "avg_latency_ms": 0,
  "success_rate": 1.0,
  "last_error": null,
  "timestamp": "2026-05-21T00:00:00Z"
}
```

## Task Contract

Remote agents receive:

```http
POST /task
```

with the JSON shape defined in `schemas/task.schema.json`. Results should match `schemas/result.schema.json`.

## Connect an External AI Through REST

```python
from ai_bridge.agents.external_ai_agent import ExternalAIAgent
from ai_bridge.core.security import SecurityManager, SecurityPolicy

security = SecurityManager(SecurityPolicy())
agent = ExternalAIAgent(
    agent_id="gemini-reviewer",
    endpoint="http://localhost:8020",
    capabilities=["review", "research"],
    security=security,
)
```

`ExternalAIAgent` sends limited task context only. Keys named like `token`, `secret`, `password`, or `key` are dropped, and string values are redacted for common secret patterns.

## Load Balancing

The balancer scores agents with:

```text
success_rate * 0.35
+ availability * 0.25
+ speed_score * 0.20
+ cost_score * 0.10
+ specialization_score * 0.10
- overload_penalty
```

It considers active tasks, queue depth, latency, success rate, token cost, last seen, and status.

## Security

`SecurityManager` provides:
- shell command allowlist validation;
- destructive command dry-run detection;
- blocked command checks;
- secret redaction for logs and external AI context.

Example:

```python
from ai_bridge.core.security import SecurityManager, SecurityPolicy

security = SecurityManager(SecurityPolicy(
    allow_shell=True,
    shell_allowlist=["pytest", "python -m pytest", "npm test"],
))
assert security.validate_shell_command("pytest ai_bridge/tests")
assert not security.validate_shell_command("sudo rm -rf /")
```



## Orchestrator Pipeline

The orchestrator uses a hybrid Waterfall + Agile flow:

```text
intake -> analysis -> decomposition -> agent_selection -> execution
-> merge_results -> tests -> review -> fixes -> final_validation -> report
```

For a planning task, `TaskDecomposer` creates atomic tasks for `plan`, `code`, `test`, and `review`. Each task is decorated with:

- `required_capability`
- `complexity`
- `assigned_model`
- `dependencies`
- `expected_output`
- `acceptance_criteria`

## Agent Lifecycle

Agents can move through these states:

```text
offline -> starting -> ready -> busy -> idle
overloaded -> degraded -> disabled -> failed
```

`AgentLifecycleManager` owns transitions. `AgentAutoscaler` disables idle non-critical agents when:

```text
idle_time_sec > idle_shutdown_sec
queue_depth == 0
active_tasks == 0
agent_type is not critical
```

If a later task needs a capability that only a disabled agent has, autoscaler re-enables that agent and waits for health readiness before routing.

Critical agents are not auto-disabled:

- planner
- main codex
- security reviewer
- orchestrator-capable agents

## Agent Metrics

`MetricsCollector` records per-agent metrics:

```text
agent_id, agent_type, model_name, provider, status,
active_tasks, completed_tasks, failed_tasks, queue_depth,
avg_latency_ms, success_rate, error_rate,
token_input, token_output, token_total, estimated_cost,
cpu_load, memory_load, last_seen, idle_time_sec, uptime_sec,
current_task_id, current_task_type,
quality_score, review_score, test_pass_rate
```

Metrics are included in orchestrator results and can be exported through `metrics.schema.json`.

## KPI Evaluation

`KPIEvaluator` computes:

```text
agent_kpi =
  quality_score * 0.30
  + test_success_rate * 0.25
  + delivery_score * 0.20
  + stability_score * 0.15
  + cost_efficiency * 0.10
```

If KPI drops below the configured threshold, Codex reduces the agent priority score. Projects can extend this to require second review or disable unstable agents.

## Model Selection

`ModelSelector` keeps the cheap path cheap and only opens the expensive path
when the task actually needs it. The router now works with provider policy, so
the selected model depends on task complexity, available providers, and the
session budget.

| Complexity | Typical work | Default direction |
| --- | --- | --- |
| Low | docs, formatting, small fixes | `local-small` or a light local provider |
| Medium | module work, tests, API changes, refactors | `mistral-small-or-medium`, with Gemini for docs/research |
| High | architecture, larger debugging, cross-module work | stronger provider choice, with OpenAI only when auto-routing is enabled |
| Critical | security, secrets, production, migrations | strongest available provider, then fallback if OpenAI is not configured |

Critical tasks should run through:

```text
planner -> codex -> reviewer -> tester -> security reviewer
```

### OpenAI Auto-Routing

If `AI_BRIDGE_OPENAI_AUTO_MODEL=true`, the runtime checks `OPENAI_API_KEY`,
discovers live models through `/v1/models`, and applies
`OPENAI_SESSION_TOKEN_BUDGET` before it picks a heavier model. The first task
in a session refreshes the catalog; later tasks can reuse the cache.

## Visible User Console

`UserConsole` records simple status events:

```text
[PLAN] Task analyzed
[AGENTS] Agents found: 4, available: 4
[ROUTING] code routed to agent codex-main
[REVIEW] Quality below threshold: low_confidence
[FIX] Errors found, a fix task was created
[DONE] All criteria satisfied
```

It can also render per-agent status:

```text
Agent: codex-main
Status: busy
Task: creating module load_balancer.py
Model: selected-per-task
Progress: 65%
Current stage: writing code
Errors: none
```

## Quality Gate

`QualityAnalyzer` checks every result for:

- done/failed status;
- confidence threshold;
- possible secret leakage;
- missing summary;
- acceptance criteria needing review.

Low quality results are routed into the feedback loop, which creates `fix` tasks until retry limits are reached.

## Known Limitations

- WebSocket protocol is a placeholder adapter; projects can extend it with their preferred client.
- The included local agents are deterministic test doubles, not full coding models.
- REST transport uses Python standard library for portability and minimal dependencies.
- No persistent database is included; registry and metrics are in-memory.

## Next Improvements

- Add persistent registry storage.
- Add async task execution and worker pools.
- Add authenticated REST server implementation for agents.
- Add real CI adapters for npm, pytest, ruff, mypy, and container checks.

## P2P Agent Messaging and Smart Scheduler

`SmartScheduler` supports a hybrid control model:

```text
Orchestrator -> strategic, high-risk, multi-system work
Scheduler -> priority, dependency, readiness, retry, escalation decisions
Agents -> local execution and low-risk P2P feedback
MessageBus -> direct or relayed P2P delivery with ACK history
```

Use orchestrator routing for architecture, API, database, auth, security, rollback, audit, and critical tasks. Low-risk local feedback can use P2P, for example:

```text
tester_agent -> coder_agent: test_failed
reviewer_agent -> coder_agent: fix_required
docs_agent -> coder_agent: request_context
monitor_agent -> scheduler_agent: agent_overloaded
```

### Readiness States

Agents can report detailed lifecycle states:

```text
offline, starting, warming_up, loading_context, loading_task_context,
ready, idle, assigned, busy, blocked, waiting_dependency, waiting_input,
reviewing, testing, degraded, overloaded, cooling_down, standby, sleeping,
unreachable, failed, recovering, draining, maintenance, disabled
```

`SmartScheduler.readiness(agent)` normalizes these into `cold`, `warm`, or `hot` start decisions using active tasks, queue depth, limits, latency, and last heartbeat.

### Task Weight

Tasks are ranked by:

```text
task_score =
  priority * 0.30
  + urgency * 0.20
  + business_value * 0.20
  + risk * 0.15
  + dependency_count * 0.10
  + complexity * 0.05
```

P0/P1-style critical work should stay under orchestrator governance. P3-P5 local tasks can use direct P2P when no architecture, security, API, database, rollback, or human approval risk is detected.

### Agent Selection

Scheduler agent scoring uses:

```text
agent_score =
  capability_match * 0.35
  + availability * 0.25
  + low_latency * 0.15
  + low_load * 0.15
  + success_rate * 0.10
```

Overloaded, failed, disabled, unreachable, draining, and maintenance agents are excluded from routing. Busy agents only receive low-cost docs/research work.

### P2P Message Example

```python
from ai_bridge.core.message_bus import MessageBus
from ai_bridge.core.models import P2PMessage, P2PMessageType

bus = MessageBus()
message = P2PMessage(
    task_id="task-123",
    from_agent="tester_agent",
    to_agent="coder_agent",
    message_type=P2PMessageType.TEST_FAILED,
    priority="high",
    payload={
        "failed_tests": ["test_auth_login"],
        "error": "Expected 200, got 401",
        "suggested_action": "check auth middleware",
    },
)

bus.send_p2p(message)
received = bus.receive_for_agent("coder_agent")
```

Important messages get ACK states:

```text
sent -> received -> accepted -> processing -> completed
failed | timeout
```

If direct delivery fails, use relay routing:

```text
tester_agent -> reviewer_agent -> coder_agent
```

When retry limits are exceeded, architecture changes, security is affected, or agent conflicts are detected, `SmartScheduler.should_escalate(...)` returns `True` and the task should return to orchestrator governance.

## Default Orchestration Mode

AI Bridge is the default orchestration core for standard safe tasks. The system should not ask `Use AI Bridge? y/n` for routine work such as code generation, tests, review, docs, refactor, local scripts, healthchecks, metrics, and task routing.

Default behavior:

```text
User task -> AI Bridge Core -> Planner -> Scheduler -> Agent Registry
-> Task Router -> Agents -> Tests -> Review -> Result Aggregation -> Done
```

Confirmation is still required for destructive, production, security-sensitive, and external side-effect operations.

### Config

```yaml
orchestration:
  enabled_by_default: true
  ask_confirmation: false
  default_mode: ai_bridge
  auto_route_tasks: true
  auto_start_agents: true
  auto_retry: true
  auto_review: true
  auto_test: true

confirmation_policy:
  ask_for_low_risk_tasks: false
  ask_for_medium_risk_tasks: false
  ask_for_high_risk_tasks: true
  ask_for_destructive_actions: true
  ask_for_external_api_calls: true
```

### CLI

```bash
python3 -m ai_bridge.scripts.run_orchestrator \
  --use-bridge \
  --auto \
  --yes \
  --non-interactive
```

### Environment

```bash
export AI_BRIDGE_ENABLED=true
export AI_BRIDGE_DEFAULT=true
export AI_BRIDGE_AUTO_APPROVE=true
export AI_BRIDGE_NON_INTERACTIVE=true
export AI_BRIDGE_CONFIRMATION_POLICY=safe-only
```

### Confirmation Rules

No prompt for safe standard tasks:

```text
code generation, tests, review, docs, refactor, local scripts,
healthcheck, metrics, task routing
```

Prompt required for guarded operations:

```text
production deploy, database delete, secret changes, key rotation,
payment or billing actions, external email, public API mutation, force push
```

Programmatic check:

```python
from ai_bridge.core.orchestration_config import OrchestrationConfig

config = OrchestrationConfig.from_env()
assert not config.should_ask_confirmation({"type": "test", "risk_level": "low"})
assert config.should_ask_confirmation({"action": "database_delete"})
```

## Third-Party AI Module Availability Checks

AI Bridge must verify whether an external AI module is available before assigning a task.

An external AI module is considered available if:

1. the endpoint responds to a healthcheck;
2. the API key or token is valid;
3. the module returns a capability list;
4. latency does not exceed the limit;
5. `error_rate` is below the allowed threshold;
6. quota/rate limits are not exhausted;
7. the module supports the required `task_type`;
8. the module is not in `disabled`, `failed`, `overloaded`, or `unreachable` state.

Each external AI module must expose:

GET /health

Expected response:

{
  "agent_id": "external-ai-1",
  "provider": "openai|anthropic|local|custom",
  "model_name": "string",
  "status": "ready|busy|degraded|offline|overloaded",
  "readiness": "cold|warm|hot",
  "capabilities": ["code", "review", "test", "docs", "research"],
  "active_tasks": 0,
  "max_tasks": 5,
  "queue_depth": 0,
  "avg_latency_ms": 250,
  "success_rate": 0.98,
  "error_rate": 0.02,
  "rate_limit_remaining": 1000,
  "quota_remaining": 100000,
  "last_error": null,
  "last_seen": "ISO-8601",
  "timestamp": "ISO-8601"
}

If the module does not support `/health`, AI Bridge must run a fallback check:

1. send a minimal ping request;
2. verify HTTP status;
3. measure latency;
4. verify response format;
5. check for authorization errors;
6. derive capabilities from config;
7. write the result to metrics and the audit trail.

Fallback ping example:

POST /v1/ping

{
  "message": "healthcheck",
  "max_tokens": 1
}

AI Bridge must not send secrets, private code, or full context during healthchecks. The check must use a minimal safe payload.

Before task assignment, Scheduler must:

1. find AI modules with the required capability;
2. check readiness;
3. check quota/rate limits;
4. check latency;
5. check `error_rate`;
6. check risk policy;
7. select the best module via `load_balancer`;
8. if the module is unavailable, select a fallback;
9. if no fallback exists, escalate to Orchestrator.

Availability statuses:

ready       - tasks can be assigned
busy        - only low-priority tasks can be assigned
degraded    - use only when no fallback exists
overloaded  - do not assign new tasks
offline     - unavailable
unreachable - endpoint does not respond
failed      - exclude from routing pool
disabled    - disabled by policy
quota_empty - cannot be used until quota is restored
auth_failed - credentials must be updated

Metrics must be collected for each external AI module:

- availability
- latency_ms
- success_rate
- error_rate
- rate_limit_remaining
- quota_remaining
- failed_healthchecks
- last_successful_call
- last_error
- current_status
- readiness
- estimated_cost

If healthchecks fail multiple times in a row, AI Bridge must:

1. mark the module as `degraded`;
2. lower its routing priority;
3. after `retry_limit`, mark it as `failed`;
4. exclude it from agent selection;
5. write an event to the audit trail;
6. try a fallback module;
7. if no fallback exists, request Orchestrator intervention.
