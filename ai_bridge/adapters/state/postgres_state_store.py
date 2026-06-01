from __future__ import annotations
import os
from typing import Any

class PostgresStateStore:
    def __init__(self) -> None:
        self.enabled = os.getenv("AI_BRIDGE_ENABLE_POSTGRES_STATE", "false").lower() in {"1","true","yes","on"}
        self.shadow = True
        self._shadow_cache: dict[str, dict[str, Any]] = {}

    def save_workflow(self, workflow_id: str, state: dict[str, Any]) -> None:
        if not self.enabled:
            return
        self._shadow_cache[workflow_id] = dict(state)

    def append_event(self, workflow_id: str, event_type: str, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return
        wf = self._shadow_cache.setdefault(workflow_id, {})
        events = wf.setdefault("events", [])
        events.append({"event_type": event_type, "payload": payload})

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        return self._shadow_cache.get(workflow_id)
