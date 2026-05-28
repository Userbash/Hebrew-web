from __future__ import annotations

import json
import logging
import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import os
import uuid
from collections import deque
from threading import Lock

from .kernel_api import KernelAPI
from .models import AgentResult, Task
from .persistent_memory import AI_BRIDGE_SCHEMA, ensure_storage_schema, normalize_database_url

logger = logging.getLogger("json_themes_module")

def atomic_write_themes(file_path: Path, data: bytes):
    dir_path = file_path.parent
    dir_path.mkdir(parents=True, exist_ok=True)
    temp_path = file_path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    
    with open(temp_path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    
    os.replace(temp_path, file_path)
    
    if hasattr(os, "O_DIRECTORY"):
        try:
            fd = os.open(str(dir_path), os.O_RDONLY | os.O_DIRECTORY)
            os.fsync(fd)
            os.close(fd)
        except OSError:
            pass

@dataclass(slots=True)
class JSONThemesModule:
    """
    Module for 'soft unloading' system activity into JSON 'themes' (traces).
    Provides persistent, color-coded trace logs for UI rendering.
    Uses ring buffer and batched async flush to prevent parallel write corruption.
    """
    name: str = "json_themes"
    storage_path: str = "memory_store/themes.json"
    _api: KernelAPI | None = None
    _events: deque = field(default_factory=lambda: deque(maxlen=1000))
    _lock: Lock = field(default_factory=Lock)
    _flush_pending: bool = False
    _database_url: str = ""
    _pg_enabled: bool = False
    _flushed_count: int = 0

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._database_url = os.getenv("AI_BRIDGE_MEMORY_DATABASE_URL", "").strip()
        self._pg_enabled = bool(self._database_url and ensure_storage_schema(self._database_url))
        target = f"postgresql:{AI_BRIDGE_SCHEMA}.json_themes" if self._pg_enabled else self.storage_path
        if self._api:
            self._api.log("info", f"[THEMES] {self.name} module active. Target: {target}")
        if not self._pg_enabled:
            self._load_existing()

    def on_unload(self) -> None:
        self.finalize()

    def _load_existing(self) -> None:
        p = Path(self.storage_path)
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                with self._lock:
                    self._events.extend(data)
            except Exception:
                pass

    def before_task(self, task: Task, context: dict[str, Any]) -> None:
        pass

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None:
        provider = str(context.get("provider") or "unknown")
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
        
        with self._lock:
            self._events.append(event)
            should_flush = len(self._events) % 5 == 0 and not self._flush_pending
            if should_flush:
                self._flush_pending = True
        
        if should_flush:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._async_flush())
            except RuntimeError:
                # No running loop, flush synchronously
                self._flush()

    async def _async_flush(self) -> None:
        # Yield to event loop to batch operations, then flush
        await asyncio.sleep(0.5)
        self._flush()

    def _flush(self) -> None:
        p = Path(self.storage_path)
        with self._lock:
            # Create a snapshot of current events
            events_snapshot = list(self._events)
            self._flush_pending = False
            
        try:
            if self._pg_enabled:
                pending_events = events_snapshot[self._flushed_count:]
                if pending_events:
                    self._flush_postgres(pending_events)
                    self._flushed_count = len(events_snapshot)
                return

            payload_bytes = json.dumps(events_snapshot, indent=2, ensure_ascii=False).encode("utf-8")
            atomic_write_themes(p, payload_bytes)
        except Exception as e:
            if self._api:
                self._api.log("error", f"[THEMES] Failed to flush themes: {e}")

    def _flush_postgres(self, events: list[dict[str, Any]]) -> None:
        import psycopg2  # type: ignore
        from psycopg2.extras import Json  # type: ignore

        dsn = normalize_database_url(self._database_url)
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                for event in events:
                    cur.execute(
                        f"""
                        INSERT INTO {AI_BRIDGE_SCHEMA}.json_themes (
                            task_id, session_id, agent_id, provider, color, status, event_payload, created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            str(event.get("task_id") or "unknown"),
                            str(event.get("session_id") or "default"),
                            event.get("agent_id"),
                            event.get("provider"),
                            event.get("color"),
                            event.get("status"),
                            Json(event),
                            event.get("timestamp"),
                        ),
                    )

    def finalize(self) -> dict[str, Any]:
        self._flush()
        return {
            "event_count": len(self._events),
            "storage": f"postgresql:{AI_BRIDGE_SCHEMA}.json_themes" if self._pg_enabled else self.storage_path,
            "status": "flushed"
        }
