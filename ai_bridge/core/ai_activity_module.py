from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .models import AgentResult, Task
from .kernel_api import KernelAPI


@dataclass(slots=True)
class AIActivityModule:
    name: str = "ai_activity"
    events: list[dict[str, Any]] = field(default_factory=list)
    by_provider: Counter[str] = field(default_factory=Counter)
    by_model: Counter[str] = field(default_factory=Counter)
    current: dict[str, Any] | None = None
    _api: KernelAPI | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", f"[ACTIVITY] {self.name} loaded and active.")

    def on_unload(self) -> None:
        self.current = None

    def before_task(self, task: Task, context: dict[str, Any]) -> None:
        self.current = {
            "task_id": task.task_id,
            "selected_provider": context.get("selected_provider"),
            "selected_model": context.get("selected_model"),
            "agent_id": context.get("agent_id"),
            "started_at": datetime.now(UTC).isoformat(),
        }
        if self._api:
            self._api.log("info", f"[ACTIVITY] Starting task {task.task_id} via {context.get('agent_id')}")

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None:
        provider = str(context.get("provider") or context.get("selected_provider") or "unknown")
        model = str(context.get("model") or context.get("selected_model") or "unknown")
        agent_id = str(context.get("agent_id") or result.agent_id)
        
        event = {
            "task_id": task.task_id,
            "agent_id": agent_id,
            "provider": provider,
            "model": model,
            "status": result.status.value,
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self.events.append(event)
        self.by_provider[provider] += 1
        self.by_model[model] += 1
        
        if self._api:
            self._api.log("info", f"[ACTIVITY] Task {task.task_id} {result.status.value} via {agent_id}")
            
        self.current = None

    def finalize(self) -> dict[str, Any]:
        report = {
            "current": self.current,
            "events": self.events,
            "by_provider": dict(self.by_provider),
            "by_model": dict(self.by_model),
            "total_tasks": len(self.events),
            "health_status": "ok" if self._api else "degraded"
        }
        if self._api:
            self._api.log("info", f"[ACTIVITY] Finalizing health status: {report['health_status']}")
        return report
