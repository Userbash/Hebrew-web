import copy
import os
import yaml
from typing import Any

class ConfigLoader:
    """
    TDD Implementation: Loads configuration with default fallback and environment overrides.
    """
    DEFAULT_CONFIG = {
        "project": {
            "name": "ai-bridge",
            "mode": "local"
        },
        "orchestrator": {
            "max_parallel_tasks": 5,
            "retry_limit": 3,
            "task_timeout_sec": 900
        },
        "orchestration": {
            "enabled_by_default": True,
            "ask_confirmation": False,
            "default_mode": "ai_bridge",
            "auto_route_tasks": True
        },
        "security": {
            "allow_shell": True,
            "shell_allowlist": ["pytest", "ruff check"],
            "block_commands": ["sudo", "rm -rf /"]
        }
    }

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path
        self._config = self._load()

    def _load(self) -> dict[str, Any]:
        config = copy.deepcopy(self.DEFAULT_CONFIG)
        
        # 1. Load from YAML if exists
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                yaml_data = yaml.safe_load(f) or {}
                self._deep_update(config, yaml_data)
        
        # 2. Environment Variable Overrides (Prefix: AI_BRIDGE_)
        # Example: AI_BRIDGE_PROJECT_NAME -> config["project"]["name"]
        self._apply_env_overrides(config)
        
        return config

    def _deep_update(self, base: dict, update: dict):
        for key, value in update.items():
            if isinstance(value, dict) and key in base:
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self, config: dict):
        """
        Maps env vars to config keys.
        AI_BRIDGE_PROJECT_NAME -> project.name
        AI_BRIDGE_ORCHESTRATOR_MAX_PARALLEL_TASKS -> orchestrator.max_parallel_tasks
        """
        mapping = {
            "AI_BRIDGE_PROJECT_NAME": ("project", "name"),
            "AI_BRIDGE_ORCHESTRATOR_MAX_PARALLEL_TASKS": ("orchestrator", "max_parallel_tasks"),
            "AI_BRIDGE_ORCHESTRATION_ENABLED_BY_DEFAULT": ("orchestration", "enabled_by_default"),
        }
        
        for env_key, config_keys in mapping.items():
            val = os.environ.get(env_key)
            if val is not None:
                # Type conversion
                if val.lower() in ("true", "false"):
                    val = val.lower() == "true"
                elif val.isdigit():
                    val = int(val)
                
                # Navigate and set
                target = config
                for k in config_keys[:-1]:
                    target = target[k]
                target[config_keys[-1]] = val

    def get_config(self) -> dict[str, Any]:
        return self._config
