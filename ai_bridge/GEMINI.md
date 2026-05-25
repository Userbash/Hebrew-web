# AI Bridge Scoped Instructions

This directory contains the AI Bridge orchestration runtime. All modifications must adhere to the **Calibration and Patch Policy**.

## Core Mandates

1.  **Never rewrite the orchestration core entirely.** Only apply surgical patches, local fixes, and isolated improvements.
2.  **Patch Policy:**
    *   Maximum 1 file, 1 module, or 1 routing rule per patch.
    *   Each patch MUST include:
        *   Root cause identification.
        *   Minimal diff.
        *   Automated test verification.
        *   Audit trail validation.
    *   NO breaking changes to public protocols or schemas without formal migration.
3.  **Validation Workflow:**
    *   `python3 -m pytest ai_bridge/tests`
    *   `python3 -m ai_bridge.scripts.run_healthcheck`
    *   Synthetic Dry Run: `python3 -m ai_bridge.scripts.run_orchestrator --use-bridge --auto --yes --non-interactive`

## Calibration Triggers

Perform calibration if:
*   Scheduler consistently selects suboptimal agents.
*   Success rate drops or latency spikes.
*   Cyclic retries occur in the Feedback Loop.
*   Metrics drift from actual runtime state.
*   QualityGate yields false positives.

## Stable Subsystems (Validated)
The following are considered production-ready and should not be modified without explicit calibration requirements:
*   Routing & Load Balancing.
*   External AI (Gemini CLI) integration.
*   Feedback Loop & Retry Management.
*   Quality Gate analysis.
*   In-memory Metrics & Audit Logging.

## Hybrid Memory Phase 1

- Added `HybridMemory` with hot in-memory cache and persistent layer via `PersistentMemoryManager`.
- Added soft eviction policy using weighted score: `0.4*recency + 0.3*access_freq + 0.3*importance`.
- `SessionMemory` now acts as a thin facade over `HybridMemory` and preserves compatibility API.
- Added command context persistence and retrieval (`command_history`) for quick context window restore.
- Added `MemoryConsolidator` for episodic memory summarization and long-term retention.
- Added SQL schema and Alembic migration for PostgreSQL + pgvector.
- `Orchestrator` now initializes dependencies via `AgentFactory` and stores execution traces in hybrid memory.
