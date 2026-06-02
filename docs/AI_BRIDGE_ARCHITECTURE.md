# AI Bridge Architecture

This is a compact architecture overview. The current provider and model routing
rules live in `AI_BRIDGE_RUNTIME_ROUTING.md`.

## What this layer does

- decomposes a root task into smaller executable pieces;
- chooses a route through the orchestrator or peer-to-peer messaging;
- selects an agent based on capability, load, and reliability;
- keeps execution safe with allowlists and secret redaction;
- verifies output before results are accepted.

## Runtime flow

1. `Orchestrator` receives a task and classifies the risk.
2. `TaskDecomposer` turns the work into `PLAN`, `CODE`, `TEST`, `REVIEW`,
   and `FIX` steps when needed.
3. `SmartScheduler` decides whether the task should stay under orchestrator
   control or go through local P2P delivery.
4. `TaskRouter` and `LoadBalancer` choose the best available agent.
5. `SecurityManager` filters shell commands and strips secrets from the
   context that is sent to external systems.
6. `QualityAnalyzer` checks the result and rejects weak output.
7. `FeedbackLoop` creates a fix task when the output fails quality checks.
8. `ResultMerger` assembles the final response.

## Component notes

### SecurityManager (`core/security.py`)

- validates shell commands against a strict allowlist;
- redacts API keys, tokens, passwords, and similar secrets;
- trims sensitive fields before sending data to external AI providers.

### LoadBalancer (`core/load_balancer.py`)

- weighs success rate, availability, latency, cost, and specialization;
- applies an overload penalty when an agent is already too busy.

### TaskDecomposer (`core/task_decomposer.py`)

- maps high-level work to the right task type;
- adds the capability and model hints needed by the router;
- keeps dependencies explicit so the DAG stays readable.

### FeedbackLoop (`core/feedback_loop.py`)

- tracks retry counts per task;
- creates a `FIX` task when the current result does not pass review;
- pushes the fix back through the router instead of patching in place.

### AuditTrail (`core/audit.py`)

- writes immutable execution records;
- keeps raw input and secrets out of the log stream;
- records the decisions that matter for later diagnosis.

## Operational notes

- dry-run paths stay in memory or in stubs;
- destructive work fails closed instead of trying to continue;
- external AI output still goes through local review before final acceptance.
