from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .kernel_api import KernelAPI
from .models import AgentResult, Task


@dataclass(slots=True)
class ModelUsageModule:
    name: str = "model_usage"
    _api: KernelAPI | None = None
    current: dict[str, Any] | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def on_load(self, api: KernelAPI) -> None:
        self._api = api

    def on_unload(self) -> None:
        self.current = None

    def before_task(self, task: Task, context: dict[str, Any]) -> None:
        self.current = {
            "task_id": task.task_id,
            "task_type": task.type.value,
            "provider": context.get("provider") or context.get("selected_provider"),
            "model": context.get("model") or context.get("selected_model"),
            "agent_id": context.get("agent_id"),
            "started_at": datetime.now(UTC).isoformat(),
        }

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None:
        record = {
            "task_id": task.task_id,
            "task_type": task.type.value,
            "provider": context.get("provider") or context.get("selected_provider"),
            "model": context.get("model") or context.get("selected_model"),
            "agent_id": context.get("agent_id") or result.agent_id,
            "status": result.status.value,
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self.history.append(record)
        self.current = None

    def finalize(self) -> dict[str, Any]:
        return {
            "current": self.current,
            "history": self.history,
            "current_model": self.current["model"] if self.current else None,
            "current_provider": self.current["provider"] if self.current else None,
        }
