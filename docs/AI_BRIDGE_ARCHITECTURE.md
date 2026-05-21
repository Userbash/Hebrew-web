# AI Bridge Orchestration Core Technical Reference

This document provides a comprehensive breakdown of the internal orchestration runtime, component architecture, and operational flow of the AI Bridge framework.

## 1. Overview
The core runtime facilitates multi-agent, distributed task execution with built-in security, quality verification, and self-healing mechanisms. It operates on an event-driven architecture using a centralized `Orchestrator` to manage complex pipelines.

## 2. Orchestration Pipeline
The execution pipeline follows a structured life cycle for every incoming request:

1.  **Intake & Classification**: The `Orchestrator` receives a `Task`. `RiskClassifier` assigns a `RiskLevel` (Safe, Moderate, High, Destructive, etc.).
2.  **Decomposition**: The `TaskDecomposer` translates complex objectives into an `ExecutionPlan`, creating a Directed Acyclic Graph (DAG) of `AtomicTask` objects with explicit dependencies.
3.  **Scheduling**: `SmartScheduler` decides whether the task is routed via the centralized `Orchestrator` or optimized for `P2P` (agent-to-agent) communication based on risk and complexity.
4.  **Routing & Load Balancing**: `TaskRouter` queries the `AgentRegistry` and `LoadBalancer` to assign the most suitable agent, based on a weighted scoring formula prioritizing quality and historical success rates.
5.  **Execution & Security**: The `Agent` executes the task. The `SecurityManager` enforces the `shell_allowlist` for local tasks and performs `redaction` (masking of secrets) for external AI agents.
6.  **Quality Assurance**: `QualityAnalyzer` evaluates the result. If parameters (e.g., `confidence`, `schema_validity`) are not met, the result is rejected.
7.  **Feedback Loop**: Upon failure or rejection, `FeedbackLoop` increments retry counters and initiates a `fix_task` (if below `retry_limit`).
8.  **Aggregation**: `ResultMerger` combines the results of all atomic tasks into a final, validated output.

## 3. Core Component Analysis

### 3.1. SecurityManager (`core/security.py`)
Acts as the final authority on system-level interactions.
- **`validate_shell_command`**: Uses a strict allowlist to permit only safe binaries.
- **`redact_secrets`**: Employs Regex patterns to scrub API keys, tokens, and passwords from logs and payload data.
- **`safe_context_for_external_ai`**: Filters out sensitive configuration keys from task payloads before dispatching to external models (Gemini/DeepSeek).

### 3.2. LoadBalancer (`core/load_balancer.py`)
Implements a decision-making engine for task routing:
- **Scoring Formula**: Aggregates `success_rate`, `availability`, `latency`, `cost`, and `capability_match`.
- **Overload Penalty**: Dynamically penalizes agents whose `active_tasks + queue_depth` exceeds the `overload_threshold` (default 0.85).

### 3.3. TaskDecomposer (`core/task_decomposer.py`)
Handles the translation of high-level goals into executable operations.
- **DAG Generation**: Maps tasks to types: `PLAN`, `CODE`, `TEST`, `REVIEW`, `FIX`, etc.
- **Decorator Logic**: Automatically attaches `required_capability` and selects the `assigned_model` based on task complexity.

### 3.4. FeedbackLoop (`core/feedback_loop.py`)
Manages task recovery.
- Maintains a registry of retry counts per `task_id`.
- If a task fails or is rejected, it automatically constructs a `FIX` task, inheriting the context and criteria of the parent task, and escalates it to the `Router`.

### 3.5. AuditTrail (`core/audit.py`)
Maintains an immutable record of execution flows.
- Logs events to `bridge_access.log`.
- Tracks `risk_level`, `auto_approval_status`, and `event_details` without ever logging raw input or secret data.

## 4. Operational Principles
- **Dry-Run Isolation**: All framework tests operate in-memory or through sandboxed stubs. The core prevents file writes when `dry_run` is detected by the `SecurityManager`.
- **Security-First Execution**: The system rejects operations involving destructive commands or unauthorized secret access, forcing a failure state rather than attempting dangerous execution.
- **Contributor-Only External AI**: External AI agents (e.g., DeepSeek, Gemini) are restricted by the policy `can_finalize=False`, ensuring that all AI-generated output is subject to local agent (Reviewer/Tester) verification before final acceptance.
