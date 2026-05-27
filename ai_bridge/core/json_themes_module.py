from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .kernel_api import KernelAPI
from .models import AgentResult, Task


@dataclass(slots=True)
class JSONThemesModule:
    """
    Module for 'soft unloading' system activity into JSON 'themes' (traces).
    Provides persistent, color-coded trace logs for UI rendering.
    """
    name: str = "json_themes"
    storage_path: str = "memory_store/themes.json"
    _api: KernelAPI | None = None
    _events: list[dict[str, Any]] = field(default_factory=list)

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", f"[THEMES] {self.name} module active. Target: {self.storage_path}")
        self._load_existing()

    def on_unload(self) -> None:
        self.finalize()

    def _load_existing(self) -> None:
        p = Path(self.storage_path)
        if p.exists():
            try:
                self._events = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                self._events = []

    def before_task(self, task: Task, context: dict[str, Any]) -> None:
        pass

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None:
        provider = str(context.get("provider") or "unknown")
        # Color mapping for 'themes'
        colors = {
            "google": "#4285F4",
            "openai": "#10a37f",
            "mistral": "#f5d142",
            "local": "#6c757d",
            "unknown": "#000000"
        }
        
        event = {
            "task_id": task.task_id,
            "session_id": task.session_id or "default",
            "agent_id": result.agent_id,
            "provider": provider,
            "color": colors.get(provider, "#000000"),
            "status": result.status.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "summary": str(result.output.get("summary", ""))[:500]
        }
        self._events.append(event)
        # Soft flush every 5 events
        if len(self._events) % 5 == 0:
            self._flush()

    def _flush(self) -> None:
        p = Path(self.storage_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Keep only last 1000 events for 'soft' storage
            trimmed = self._events[-1000:]
            p.write_text(json.dumps(trimmed, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            if self._api:
                self._api.log("error", f"[THEMES] Failed to flush themes: {e}")

    def finalize(self) -> dict[str, Any]:
        self._flush()
        return {
            "event_count": len(self._events),
            "storage": self.storage_path,
            "status": "flushed"
        }
