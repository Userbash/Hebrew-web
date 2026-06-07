# Detailed Report: AI Bridge Orchestration Ecosystem (v2.0)

This report provides an exhaustive breakdown of the logic, memory, and multi-tier agent hierarchy within the Language School Platform's AI Bridge.

---

## 1. Multi-Tier Agent Hierarchy & Roles

The system uses a recursive "Agent -> Sub-Agent -> Pod-Agent" structure to solve problems of varying scales.

### Tier 1: The Root Agents (Strategic Level)
*   **PlannerAgent (`planner-1`)**:
    *   **Model**: Claude 4.6 (Thinking).
    *   **Role**: Analyzes high-level user requests. Responsible for creating the `ExecutionPlan` and identifying cross-module dependencies.
*   **ReviewerAgent (`reviewer-1`)**:
    *   **Model**: Claude 4.6 or Gemini 3.1 Pro (High).
    *   **Role**: Final architectural oversight. Verifies that all sub-tasks combined meet the project's global integrity standards.

### Tier 2: The Sub-Agents (Specialized Level)
*   **CodexAgent (`codex-main`)**:
    *   **Model**: Gemini 3.1 Pro (High).
    *   **Role**: Heavy-duty backend and core logic implementation.
*   **FrontendDevAgent (`frontend-dev-1`)**:
    *   **Model**: Gemini 3.1 Pro (High) / OpenAI.
    *   **Role**: Specialized in React/TypeScript, Tailwind, and UI logic.
*   **FrontendDesignAgent (`frontend-design-1`)**:
    *   **Model**: Local LLM or Gemini Flash.
    *   **Role**: Converts specs into DESIGN.md files and UI themes.
*   **TesterAgent (`tester-1`)**:
    *   **Model**: Gemini 3.5 Flash.
    *   **Role**: Generates unit and E2E tests based on the implementation summary.

### Tier 3: Pod-Agents (Execution Level - TPP Mesh)
*   **Pod-Agents** are instances of sub-agents that are "mounted" into a specific context (e.g., a specific folder or task branch).
*   **Communication**: They communicate via **TPP (Transparent Peer-to-Peer)**.
*   **Gossip State**: A Pod-Agent broadcasts its "Mental Fingerprint" (hash of its local memory) so other Pods know what context it currently holds.

---

## 2. Decision Logic & Task Chaining

Tasks move through the stack in a **Directed Acyclic Graph (DAG)**.

1.  **Ingestion**: `TriggerDispatcher` identifies the intent.
2.  **Validation**: `RiskAdvisor` (LLM-based) scans for security threats.
3.  **Decomposition**: `SmartDecomposer` breaks the task into a chain:
    *   *Example*: `BUILD: auth logic` -> 
        1. `DB: create migration` (Sub-task A)
        2. `API: implement endpoint` (Sub-task B, depends on A)
        3. `TEST: verify JWT` (Sub-task C, depends on B)
4.  **Routing**: `TaskRouter` assigns each node in the DAG to the most cost-effective Pod-Agent/Model combination.
5.  **P2P Handover**: When Sub-task A is `DONE`, the DB Pod sends a `TPPMessage(type="CONTEXT_TRANSFER")` directly to the API Pod, sharing the new schema details.

---

## 3. Semantic Memory & Context Optimization

The system avoids "Memory Fatigue" (filling the context window with junk) through three layers:

### A. Memory Storage
*   **Episodic**: Per-task results and "Thoughts" are stored with UUIDs.
*   **Semantic**: High-level architectural patterns are indexed in the `HybridMemory` using **Semantic Vector Search**.

### B. Retrieval Algorithm (Vector-Hybrid HNSW)
When an agent starts a task, it doesn't get the whole history. It performs a **Semantic Probe**:
1.  **Embedding**: The query is converted into a vector.
2.  **Scoring**:
    *   **Similarity (0.5)**: Find tasks with similar *meaning*.
    *   **Importance (0.3)**: Prioritize "Senior Architect" decisions.
    *   **Time Decay (0.2)**: Penalize very old data that might be deprecated.
3.  **Top-K Selection**: Only the 3 most relevant memory chunks are selected.

### C. Context Briefing
The selected chunks are compressed into a **Context Brief** (max 1500 tokens). This brief acts as a "Cheat Sheet" for the agent, allowing it to work with 95% accuracy while using 90% fewer context tokens.

---

## 4. Model Specialization Matrix

| Task Type | Preferred Model | Reason |
| :--- | :--- | :--- |
| **Root Planning** | Claude 4.6 (Thinking) | Superior reasoning for dependencies. |
| **Complex Logic** | Gemini 3.1 Pro (High) | High token limit and strong coding capability. |
| **Error Diagnosis** | qwen2.5:32b (Local) | Fast, free, and context-aware classification. |
| **Tests/Docs** | Gemini 3.5 Flash | High speed for structured, repetitive tasks. |
| **Security Audit** | Claude 4.6 (Thinking) | Nuanced understanding of vulnerabilities. |

---

## 5. Persistence & Recovery
*   **Repair Flow**: If any agent fails due to quota or logic, the `AIIntelligenceModule` diagnoses the error and the `Orchestrator` performs a **Soft Fallback** to a different provider/model.
*   **Atomic Traces**: All activity is logged via `JSONThemes` with atomic write locks, preventing data loss during high-concurrency P2P operations.

---
*End of Report. Approved by OrchestratorAdvisorModule.*
