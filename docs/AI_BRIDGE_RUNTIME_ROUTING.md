# AI Bridge Runtime Routing

This is the current reference for AI Bridge model choice and provider routing.
It covers the code paths that changed most recently and the rules that now
control token use, fallback order, and per-task model selection.

## What this doc covers

- task complexity classification;
- provider selection across OpenAI, Gemini, Mistral, and local fallback;
- session token budgeting for OpenAI use;
- live model discovery through `GET /v1/models`;
- the runtime cache used when OpenAI is enabled;
- the parts of the orchestrator that now consume the selected model.

## Current routing flow

1. `ModelSelector` classifies the task as low, medium, high, or critical.
2. If OpenAI auto-routing is enabled and an `OPENAI_API_KEY` is available,
   `OpenAIModelRegistry` refreshes the model catalog from the OpenAI API and
   caches the result locally.
3. `OpenAIRuntimeRouter` builds an ordered list of candidates for the task,
   using the task complexity, prompt size, and the remaining session budget.
4. `ProviderBudgetRouter` keeps the task on the cheapest viable provider when
   OpenAI is not needed or not available.
5. `CodexAgent` uses the selected model for that task instead of one global
   model for the whole process.

The main goal is simple: use expensive models only when the task really needs
them, and keep the fallback path predictable when the environment does not have
OpenAI access.

## Complexity bands

| Complexity | Default direction | Notes |
| --- | --- | --- |
| Low | local or lightweight provider | Used for short docs, formatting, and small fixes. |
| Medium | Mistral first, then Gemini or lightweight OpenAI if enabled | Keeps the common path cheap. |
| High | stronger provider selection, OpenAI only when the key and budget allow it | Used for architecture, larger refactors, and hard debugging. |
| Critical | strongest available route, with fallback if OpenAI is not configured | Used for security, production, migrations, and other risky work. |

## OpenAI auto-routing

The OpenAI path is opt-in through environment variables. When it is enabled,
the runtime does not guess model names from hard-coded lists alone. It first
looks at the live model list returned by the account.

### Runtime modules

- `ai_bridge/core/openai_model_registry.py`
  - `OpenAIModelRegistry.get_models(force_refresh=False)`
  - `OpenAIModelRegistry.get_catalog(force_refresh=False)`
- `ai_bridge/core/openai_runtime_router.py`
  - `OpenAIRuntimeRouter.build_plan(task, prompt="")`
  - `OpenAIRuntimeRouter.select_model(task, prompt="")`
  - `OpenAIRuntimeRouter.register_usage(task, consumed_tokens)`
  - `OpenAIRuntimeRouter.block_model(task, model)`

### Environment variables

- `AI_BRIDGE_OPENAI_AUTO_MODEL`
  - Enables the OpenAI routing layer when set to a truthy value.
- `OPENAI_API_KEY`
  - Required for live model discovery.
- `OPENAI_SESSION_TOKEN_BUDGET`
  - Caps the approximate token budget for a session.
- `OPENAI_LOW_MODELS`
  - Optional override list for low-complexity tasks.
- `OPENAI_MEDIUM_MODELS`
  - Optional override list for medium-complexity tasks.
- `OPENAI_HIGH_MODELS`
  - Optional override list for high-complexity tasks.
- `OPENAI_CRITICAL_MODELS`
  - Optional override list for critical tasks.
- `OPENAI_EXTRA_MODELS`
  - Extra fallback models appended to every tier.
- `OPENAI_MODELS_CACHE_PATH`
  - Path for the cached model list.
- `OPENAI_MODELS_CACHE_TTL_SEC`
  - Cache lifetime in seconds.

## Notes on the cache

The registry stores the last known model list in
`ai_bridge/.cache/openai_models.json` unless `OPENAI_MODELS_CACHE_PATH` points
somewhere else. If the cache is still valid, the router can keep working even
when live discovery is temporarily unavailable.

## What changed in the code

- The orchestrator now treats provider choice as a per-task decision.
- The model router respects session budget before selecting a heavier model.
- The fallback path no longer depends on one provider being present.
- The repo now has a live model inventory step instead of a fixed model list.

## How this fits the rest of the docs

- `docs/ARCHITECTURE.md` gives the system-wide view.
- `docs/AI_BRIDGE_ARCHITECTURE.md` describes the AI Bridge components at a
  higher level.
- `docs/AI_ORCHESTRATOR_CORE.md` keeps the deeper technical reference.
- This file is the current place to check for model choice and provider rules.
