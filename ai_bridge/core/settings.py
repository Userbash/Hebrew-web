from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .config import ConfigLoader


class ProjectSettings(BaseModel):
    name: str = "ai-bridge"
    mode: str = "local"


class OrchestratorSettings(BaseModel):
    max_parallel_tasks: int = 5
    retry_limit: int = 3
    task_timeout_sec: int = 900


class OrchestrationSettings(BaseModel):
    enabled_by_default: bool = True
    ask_confirmation: bool = False
    default_mode: str = "ai_bridge"
    auto_route_tasks: bool = True
    auto_start_agents: bool = True
    auto_retry: bool = True
    auto_review: bool = True
    auto_test: bool = True


class AgentSettings(BaseModel):
    id: str
    type: str
    endpoint: str
    capabilities: list[str] = Field(default_factory=list)


class LoadBalancingSettings(BaseModel):
    strategy: str = "weighted_score"
    healthcheck_interval_sec: int = 30
    overload_threshold: float = 0.85


class SecuritySettings(BaseModel):
    allow_shell: bool = True
    shell_allowlist: list[str] = Field(default_factory=lambda: ["pytest", "ruff check", "python -m pytest"])
    block_commands: list[str] = Field(default_factory=lambda: ["sudo", "rm -rf /"])


class BridgeSettings(BaseModel):
    project: ProjectSettings = Field(default_factory=ProjectSettings)
    orchestrator: OrchestratorSettings = Field(default_factory=OrchestratorSettings)
    orchestration: OrchestrationSettings = Field(default_factory=OrchestrationSettings)
    agents: list[AgentSettings] = Field(default_factory=list)
    load_balancing: LoadBalancingSettings = Field(default_factory=LoadBalancingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "BridgeSettings":
        return cls.model_validate(ConfigLoader(str(config_path) if config_path else None).get_config())

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
