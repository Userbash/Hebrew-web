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

`ModelSelector` maps task complexity to models:

| Complexity | Example | Model |
| --- | --- | --- |
| Low | docs, formatting, small fixes | `local-small` |
| Medium | module, tests, API, refactor | `gpt-coding-standard` |
| High | architecture, distributed debugging | `gpt-coding-large` |
| Critical | security, secrets, production, migrations | `gpt-senior-secure` |

Critical tasks should run through:

```text
planner -> senior codex -> reviewer -> tester -> security reviewer
```

## Visible User Console

`UserConsole` records simple status events:

```text
[PLAN] Задача проанализирована
[AGENTS] Найдено агентов: 4, доступно: 4
[ROUTING] code передан агенту codex-main
[REVIEW] Качество ниже порога: low_confidence
[FIX] Найдены ошибки, создана задача исправления
[DONE] Все критерии выполнены
```

It can also render per-agent status:

```text
Агент: codex-main
Статус: busy
Задача: создание модуля load_balancer.py
Модель: gpt-coding-large
Прогресс: 65%
Текущий этап: пишет код
Ошибки: нет
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
