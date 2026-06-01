from __future__ import annotations
from typing import Any

class MemoryWorkflowStateStore:
    def __init__(self) -> None:
        self.workflows: dict[str, dict[str, Any]] = {}
        self.events: dict[str, list[dict[str, Any]]] = {}
    def save_workflow(self, workflow_id: str, state: dict[str, Any]) -> None:
        self.workflows[workflow_id] = dict(state)
    def append_event(self, workflow_id: str, event_type: str, payload: dict[str, Any]) -> None:
        self.events.setdefault(workflow_id, []).append({"event_type": event_type, "payload": payload})
    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        return self.workflows.get(workflow_id)
