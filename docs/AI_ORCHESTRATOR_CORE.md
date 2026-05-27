# AI Orchestrator: Core Technical Reference

This document serves as the definitive guide to the internal mechanics, component architecture, and operational logic of the AI Orchestrator Core.

## 1. Design Philosophy
The system is built on a **Modular Kernel** architecture. The `Orchestrator` acts as the central bus, while specialized logic is offloaded to independent modules and agents. Reliability is enforced through a multi-stage pipeline: **Intake -> Decomposition -> Routing -> Execution -> Validation -> Consolidation**.

## 2. Core Component Directory

### Orchestrator (`core/orchestrator.py`)
The primary runtime engine. It initializes the component tree and orchestrates the execution of both atomic tasks and complex task graphs (DAGs).
- **`run_task(task)`**: The atomic execution unit. Handles pre-flight checks, model selection, routing to a specific agent, execution, quality analysis, and potential auto-fix loops.
- **`run(root_task)`**: The entry point for complex operations. Decomposes the root goal and executes the resulting dependency graph, ensuring tasks run in the correct order.
- **`submit_user_task(payload)`**: Normalizes raw user input into a formal `Task` object before triggering the execution pipeline.

### ModelSelector (`core/model_selector.py`)
The brain behind model routing. It analyzes task requirements against a set of heuristic rules and risk markers.
- **`classify(task)`**: Categorizes tasks into `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` complexity. It flags tasks involving security, database migrations, or payments as high-risk.
- **`select(task)`**: Uses a weighted scoring algorithm to pick the best model/provider. Factors include capability match (e.g., Codestral for coding), historical reliability, and latency.

### HybridMemory (`core/hybrid_memory.py`)
A dual-layer memory system providing low-latency access and long-term persistence.
- **Hot Layer**: In-memory cache for high-frequency access during a session.
- **Persistent Layer**: Synchronous file-based storage ensuring data survives process restarts.
- **`soft_flush()`**: Synchronizes the hot layer with persistent storage.
- **Maintenance Loop**: A background task that periodically evicts stale data based on a recency/importance score.

### TaskRouter & SmartScheduler (`core/task_router.py`, `core/smart_scheduler.py`)
Handles the assignment of tasks to specific agent instances.
- **Economy Policy**: Prevents over-usage of expensive models (like GPT-4) for low-complexity tasks.
- **Routing**: Matches required capabilities (code, test, review) to available agents in the `AgentRegistry`.
- **P2P vs Orchestrator**: Small, low-risk tasks may use direct agent communication, while strategic tasks always route through the central Orchestrator for full auditing.

### SecurityGate (`core/security_gate/`)
Enforces the "Security-First" mandate.
- **Allowlist Validation**: Restricts shell commands to a predefined set of safe binaries.
- **Redaction**: Automatically masks API keys and credentials in all logs and task context before they are sent to external AI providers.

## 3. The Execution Pipeline (Step-by-Step)

1.  **Normalization**: Raw input is turned into a `Task` with defined files, constraints, and criteria.
2.  **Risk Analysis**: Keywords are scanned to detect high-risk operations (e.g., `destructive`, `production`).
3.  **Decomposition**: High-level plans are split into `PLAN -> CODE -> TEST -> REVIEW` cycles.
4.  **Routing**: The `ModelSelector` picks a model (e.g., `gemini-1.5-pro`), and the `TaskRouter` finds a specific agent (e.g., `mistral-1`).
5.  **Context Injection**: `HybridMemory` injects relevant historical data or thoughts into the task prompt.
6.  **Execution**: The agent performs the work (local script execution or external API call).
7.  **Quality Check**: The `QualityAnalyzer` verifies the output against the task's acceptance criteria.
8.  **Feedback**: If criteria are not met, a `FIX` task is generated and re-inserted into the loop.
9.  **Consolidation**: Final results and "thoughts" are saved back to memory.

## 4. Key Improvements & Stability Fixes

### Synchronous Memory Runtime
To prevent deadlocks and `RuntimeWarnings` caused by nested event loops, the memory layer (`PersistentMemoryManager`) is now **fully synchronous**. This ensures that disk I/O does not block or conflict with the asynchronous `TaskListener` or API Bridge.

### Robust Provider Fallback
The `ExternalAIBridge` now handles environment-specific failures gracefully. If a host-level binary (like `npx`) is missing, the system automatically falls back to local execution. It also classifies errors (quota, timeout, auth) to inform future routing decisions.

### Model Routing Accuracy
Futuristic or non-existent model names have been replaced with stable, verified identifiers:
- `gemini-3-flash-preview` (Default for high-speed tasks)
- `gemini-1.5-pro` (Detailed research)
- `codestral-latest` (Specialized coding agent)
- `gpt-4o` (High-accuracy fallback)

## 5. Maintenance & Debugging
- **`verify_core.py`**: A comprehensive health check script that verifies module wiring, security gates, and API connectivity.
- **`repoins.py`**: A broadcast utility that sends an inspection task to **every** registered agent. This is the fastest way to verify the entire system's operational readiness.
- **`orchestrator.log`**: Centralized log file tracking all kernel activities and task transitions.

## 6. Extending the System
To add a new agent, inherit from `BaseAgent` and use `orchestrator.attach_local_agent()`. The core will automatically begin including the new agent in the routing pool based on its declared capabilities.
