# AI Bridge Structure

## Canonical layout

- `ai_bridge/core/` - kernel runtime, routing, memory, policy, modules, adapters, and health checks.
- `ai_bridge/agents/` - agent implementations only.
- `ai_bridge/protocols/` - transport/protocol definitions.
- `ai_bridge/scripts/` - executable entrypoints, maintenance tools, smoke tests, and host bridge shims.
- `ai_bridge/db/` - persistence models and DB session helpers.
- `ai_bridge/adapters/` - integration adapters for runtime, memory, orchestration, scheduling, and models.
- `ai_bridge/schemas/` - JSON schema contracts.

## Canonical runtime entrypoints

- `ai_bridge/scripts/orchestrator_daemon.py` - main orchestrator process.
- `ai_bridge/scripts/run_orchestrator.py` - interactive/manual orchestrator runner.
- `ai_bridge/scripts/verify_core.py` - consistency and module wiring probe.
- `ai_bridge/core/core_healthcheck.py` - operational readiness probe.
- `ai_bridge/scripts/deploy_local_llm.py` - host-side local Ollama provisioning.
- `ai_bridge/scripts/host_bridge_cli.py` and `ai_bridge/scripts/bridge/exec.sh` - host bridge command execution.

## Legacy entrypoints kept for compatibility

These are not part of the preferred path, but they still exist so older automation does not break:


## Deprecated but still referenced by docs or wrappers

These should be reviewed next, but not removed blindly:

- `ai_bridge/scripts/prepare_clean_env.py`
- `ai_bridge/scripts/pre_deploy_check.py`
- `ai_bridge/scripts/pre_deploy_security_check.py`
- `ai_bridge/scripts/run_healthcheck.py`
- `ai_bridge/scripts/run_tests.py`
- `ai_bridge/scripts/run_sourcecraft_smoke.py`
- `ai_bridge/scripts/repoins.py`
- `ai_bridge/scripts/check-bridges.sh`

## Current kernel modules loaded on boot

The orchestrator currently autoloads the following modules:

- `ai_activity`
- `orchestrator_control`
- `model_usage`
- `model_availability`
- `api_bridge`
- `smart_decomposer`
- `prompt_optimizer`
- `chat_bus`
- `trigger_dispatcher`
- `json_themes`
- `unified_vfs`
- `cold_boot`
- `ui_design_system`
- `ui_anti_template`
- `frontend_engineering_bridge`
- `autodev_pipeline`
- `dev_toolkit`
- `local_llm`
- `sourcecraft`
- `voice_listener`

## Notes

- The runtime path should stay: `scripts/start_ai_bridge_stack.sh` for compose-based startup, or `scripts/start_manual.sh` for the older host-Podman route.
- Do not move or delete legacy scripts until their call sites are audited. Wrap them first, then retire them.
