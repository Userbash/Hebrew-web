# AI Orchestrator Core

This is the deeper technical reference for the orchestration runtime. The
current provider and model routing policy is documented in
`AI_BRIDGE_RUNTIME_ROUTING.md`.

## Design approach

The runtime is built around a modular orchestrator. The orchestrator handles
intake, decomposition, routing, execution, validation, and consolidation.
Specialized modules own the details so the core flow stays predictable.

## Core components

### Orchestrator (`core/orchestrator.py`)

- `run_task(task)` handles the full single-task flow from preflight to result.
- `run(root_task)` executes a decomposed task graph in dependency order.
- `submit_user_task(payload)` turns raw user input into a `Task`.

### ModelSelector (`core/model_selector.py`)

- classifies work into `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`;
- uses task shape, risk, and provider policy to pick the route;
- now works together with the OpenAI runtime router when auto-routing is on.

### OpenAIModelRegistry (`core/openai_model_registry.py`)

- fetches the live OpenAI model list when `OPENAI_API_KEY` is present;
- filters out non-text models;
- caches the result so the runtime does not call the API on every task.

### OpenAIRuntimeRouter (`core/openai_runtime_router.py`)

- builds an ordered model plan for the current task;
- estimates prompt and completion token use;
- blocks models that already failed in the current session;
- keeps the session budget in view before it picks a heavier model.

### TaskRouter and SmartScheduler (`core/task_router.py`, `core/smart_scheduler.py`)

- assign tasks to agents by capability and availability;
- keep small safe work on cheaper paths;
- keep strategic work under orchestrator control.

### SecurityGate (`core/security_gate/`)

- validates shell commands against a safe allowlist;
- redacts secrets before data leaves the local runtime;
- keeps external AI providers away from raw credentials except approved runtime variables passed through controlled adapters.

## Execution pipeline

1. Normalize the incoming request into a `Task`.
2. Classify the risk and complexity of the task.
3. Split the work into `PLAN`, `CODE`, `TEST`, and `REVIEW` steps where needed.
4. Choose the provider model and the target agent; Google CLI routes resolve to `antigravity-cli`/`agy`.
5. Inject safe context into the task prompt.
6. Execute the task and collect the result.
7. Run quality checks against the acceptance criteria.
8. Create a `FIX` task if the result is not good enough.
9. Store the final output and the relevant execution notes.

## Stability notes

- memory operations stay synchronous to avoid nested event-loop problems;
- provider fallback is designed to fail closed into a local path instead of
  breaking the task;
- model names are taken from the live account model list when auto-routing is
  enabled.

## Maintenance

- `verify_core.py` checks wiring, security gates, and API connectivity;
- `repoins.py` sends an inspection task to every registered agent;
- `orchestrator.log` carries the main execution trace.

## Extending the system

New agents should be registered with their capabilities first. The router then
adds them to the pool when the declared capability matches the task.

## Standalone compose stack

For a self-contained runtime that launches the orchestrator and local Ollama together, use:

```bash
./scripts/start_ai_bridge_stack.sh
```

This stack uses `docker-compose.ai.yml` and starts:
- `ollama` with the default local model pulled on boot;
- `orchestrator` with `AI_BRIDGE_LOCAL_LLM_ENDPOINT=http://ollama:11434`;
- separate named volumes for Ollama data and AI Bridge memory.

