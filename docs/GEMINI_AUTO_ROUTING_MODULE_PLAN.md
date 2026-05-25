# Gemini Auto Routing Module Plan

## Decomposition (Micro Tasks)

1. Add runtime router module for Gemini model selection by task complexity.
2. Add session token budget accounting and usage tracking.
3. Add bridge-level fallback handling for capacity exhaustion (429).
4. Add token-limit fallback handling (switch model when token errors happen).
5. Integrate router into `GeminiCLIAgent` execution path.
6. Add tests for complexity routing, usage accounting, and bridge fallback.
7. Add health signals for provider readiness in `core_healthcheck`.

## Encapsulation by AI Agents

- PlannerAgent:
  - Own dependency graph and rollout order for module tasks.
  - Track risk matrix: capacity errors, token depletion, model drift.

- CodexAgent:
  - Implement `gemini_runtime_router.py`.
  - Integrate into `external_ai_bridge.py` and `gemini_cli_agent.py`.
  - Ensure compatibility with existing shell security policy.

- TesterAgent:
  - Add and run tests:
    - `test_gemini_runtime_router.py`
    - `test_external_ai_bridge.py`
  - Verify no regressions in full `ai_bridge/tests` suite.

- ReviewerAgent:
  - Validate fallback safety and deterministic behavior.
  - Validate token accounting and no secret leakage in errors/logs.

- DocsAgent:
  - Document routing logic, model tiers, and operational env vars.
  - Add failure taxonomy for 429/capacity/token exhaustion.

- GeminiCLIAgent / MistralAgent (sub-agents):
  - Runtime contributors only; no finalize rights.
  - Gemini: execute prompt via bridge with dynamic model sequence.
  - Mistral: standby fallback provider for non-Gemini paths.

## Decapsulation (Unified Ready Variant)

R1 (implemented):
- Complexity-based Gemini model router.
- Session token-budget tracking.
- Automatic model fallback for 429 capacity and token-limit errors.
- Bridge + agent integration and tests.

R2:
- R2-GEM-01 Migrate deprecated `google.generativeai` SDK.
- Dynamic token estimation from structured output metadata.
- Multi-provider fallback chain (Gemini -> Mistral -> local).

R2 decomposition (encapsulated by agents):
- PlannerAgent: split migration by API surface and release gates.
- CodexAgent: replace SDK usage in existing Gemini modules (`agents/gemini_agent.py`, bridge adapters), no new modules.
- TesterAgent: add compatibility tests for generation and timeout handling.
- ReviewerAgent: validate auth/quota/timeout failure taxonomy parity before/after migration.
- DocsAgent: update migration notes and rollback path in existing docs.
- GeminiCLIAgent/MistralAgent: runtime-only validation, no finalize rights.

R2 decapsulation (unified ready variant):
- Existing Gemini-related modules are modified in place under orchestrator flow.
- Error taxonomy unified: tcp_timeout/api_timeout/sdk_hang/quota_exhaustion/auth_fail.
- Fallback path ready: Gemini timeout => Mistral => local agent.

R3:
- Cost-aware routing and SLO-based adaptive retry windows.

R4:
- Distributed shared budget store across workers (Redis backend).
