from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .kernel_api import KernelAPI
from .models import AgentResult, Task


@dataclass(slots=True)
class OrchestratorControlModule:
    name: str = "orchestrator_control"
    _api: KernelAPI | None = None
    submitted_total: int = 0
    finished_total: int = 0
    failed_total: int = 0
    submissions: dict[str, dict[str, Any]] = field(default_factory=dict)

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", "[CONTROL] orchestrator_control loaded")

    def on_unload(self) -> None:
        self._api = None

    def register_submission(self, task: Task, source: str = "user") -> None:
        now = datetime.now(UTC).isoformat()
        self.submitted_total += 1
        self.submissions[task.task_id] = {
            "task_id": task.task_id,
            "source": source,
            "description": task.input.description,
            "type": task.type.value,
            "priority": task.priority.value,
            "status": "submitted",
            "created_at": now,
            "updated_at": now,
            "orchestrator_source_of_truth": True,
        }

    def before_task(self, task: Task, context: dict[str, Any]) -> None:
        item = self.submissions.get(task.task_id)
        now = datetime.now(UTC).isoformat()
        if item is None:
            item = {
                "task_id": task.task_id,
                "source": "internal",
                "description": task.input.description,
                "type": task.type.value,
                "priority": task.priority.value,
                "created_at": now,
                "orchestrator_source_of_truth": True,
            }
            self.submissions[task.task_id] = item
        item["status"] = "running"
        item["agent_id"] = context.get("agent_id")
        item["updated_at"] = now

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None:
        item = self.submissions.get(task.task_id)
        now = datetime.now(UTC).isoformat()
        if item is None:
            item = {
                "task_id": task.task_id,
                "source": "internal",
                "description": task.input.description,
                "type": task.type.value,
                "priority": task.priority.value,
                "created_at": now,
                "orchestrator_source_of_truth": True,
            }
            self.submissions[task.task_id] = item

        status = result.status.value
        item["status"] = status
        item["agent_id"] = result.agent_id
        item["updated_at"] = now
        item["summary"] = str(result.output.get("summary", ""))

        self.finished_total += 1
        if status != "done":
            self.failed_total += 1

    def task_status(self, task_id: str) -> dict[str, Any] | None:
        return self.submissions.get(task_id)

    def finalize(self) -> dict[str, Any]:
        return {
            "submitted_total": self.submitted_total,
            "finished_total": self.finished_total,
            "failed_total": self.failed_total,
            "active_tasks": [item for item in self.submissions.values() if item.get("status") == "running"],
            "tasks": self.submissions,
            "source_of_truth": "orchestrator",
        }
