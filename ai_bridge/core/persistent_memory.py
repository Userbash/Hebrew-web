from __future__ import annotations

import hashlib
import json
import logging
from uuid import uuid4
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MemoryRecord:
    memory_id: int
    session_id: str
    agent_id: str
    memory_type: str
    content: Any
    metadata: dict[str, Any]
    importance_score: float = 0.5
    created_at: str = ""
    updated_at: str = ""


class PersistentMemoryManager:
    """
    High-speed File-based Memory Manager.
    PostgreSQL integration has been completely removed.
    """

    def __init__(self, settings: Any = None) -> None:
        _ = settings
        configured_dir = os.getenv("AI_BRIDGE_MEMORY_STORE_DIR", "").strip()
        if configured_dir:
            self.storage_dir = Path(configured_dir)
        else:
            app_dir = Path("/app")
            self.storage_dir = app_dir / "memory_store" if app_dir.exists() and os.access(app_dir, os.W_OK) else Path.cwd() / "memory_store" / f"run_{uuid4().hex}"

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        (self.storage_dir / "memories").mkdir(exist_ok=True)
        (self.storage_dir / "commands").mkdir(exist_ok=True)
        self.index_file = self.storage_dir / "memory_index.json"
        self.session_map_file = self.storage_dir / "session_map.json"
        if not self.index_file.exists():
            self.index_file.write_text("[]", encoding="utf-8")
        if not self.session_map_file.exists():
            self.session_map_file.write_text("{}", encoding="utf-8")

        self._records: list[dict[str, Any]] = self._read_json(self.index_file, default=[])
        self._by_sat: dict[tuple[str, str, str], list[int]] = {}
        self._by_satk: dict[tuple[str, str, str, str], list[int]] = {}
        self._max_memory_id = 0
        for idx, row in enumerate(self._records):
            self._index_record(row, idx)
            self._max_memory_id = max(self._max_memory_id, int(row.get("memory_id", 0)))

        logger.info("[MEMORY] Operating in high-speed File-based mode (No DB).")

    async def upsert_session(self, session_id: str, *, agent_id: str) -> str:
        _ = agent_id
        mapping = self._read_json(self.session_map_file, default={})
        if session_id in mapping:
            return str(mapping[session_id])
        normalized = f"sess-{hashlib.sha256(session_id.encode('utf-8')).hexdigest()[:16]}"
        mapping[session_id] = normalized
        self._write_json(self.session_map_file, mapping)
        return normalized

    async def store_memory(self, *, session_id: str, agent_id: str, memory_type: str, content: Any, **kwargs: Any) -> int:
        normalized_session_id = await self.upsert_session(session_id, agent_id=agent_id)
        now_iso = datetime.now(UTC).isoformat()
        memory_id = self._max_memory_id + 1
        record = {
            "memory_id": memory_id,
            "session_id": normalized_session_id,
            "source_session_id": session_id,
            "agent_id": agent_id,
            "memory_type": memory_type,
            "content": content,
            "metadata": kwargs.get("metadata") or {},
            "importance_score": float(kwargs.get("importance_score", 0.5)),
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        self._records.append(record)
        self._index_record(record, len(self._records) - 1)
        self._max_memory_id = memory_id
        self._write_json(self.index_file, self._records)

        self._write_json(
            self.storage_dir / "memories" / f"{memory_id}.json",
            {
                "memory_id": memory_id,
                "session_id": normalized_session_id,
                "source_session_id": session_id,
                "agent_id": agent_id,
                "type": memory_type,
                "content": content,
                "created_at": now_iso,
            },
        )
        return memory_id

    async def retrieve_memories(self, *, session_id: str, agent_id: str, memory_type: str, top_k: int = 8) -> list[MemoryRecord]:
        normalized_session_id = await self.upsert_session(session_id, agent_id=agent_id)
        sat = (normalized_session_id, agent_id, memory_type)
        indexes = self._by_sat.get(sat, [])
        filtered = [self._records[idx] for idx in reversed(indexes)]
        return [
            MemoryRecord(
                memory_id=int(row.get("memory_id", 0)),
                session_id=str(row.get("session_id", "")),
                agent_id=str(row.get("agent_id", "")),
                memory_type=str(row.get("memory_type", "")),
                content=row.get("content"),
                metadata=dict(row.get("metadata") or {}),
                importance_score=float(row.get("importance_score", 0.5)),
                created_at=str(row.get("created_at", "")),
                updated_at=str(row.get("updated_at", "")),
            )
            for row in filtered[: max(1, int(top_k))]
        ]

    async def retrieve_memory_by_key(self, *, session_id: str, agent_id: str, memory_type: str, key: str) -> MemoryRecord | None:
        normalized_session_id = await self.upsert_session(session_id, agent_id=agent_id)
        satk = (normalized_session_id, agent_id, memory_type, key)
        indexes = self._by_satk.get(satk, [])
        if not indexes:
            return None
        row = self._records[indexes[-1]]
        return MemoryRecord(
            memory_id=int(row.get("memory_id", 0)),
            session_id=str(row.get("session_id", "")),
            agent_id=str(row.get("agent_id", "")),
            memory_type=str(row.get("memory_type", "")),
            content=row.get("content"),
            metadata=dict(row.get("metadata") or {}),
            importance_score=float(row.get("importance_score", 0.5)),
            created_at=str(row.get("created_at", "")),
            updated_at=str(row.get("updated_at", "")),
        )

    async def touch_memory(self, memory_id: int, *, importance_delta: float = 0.0) -> None:
        now_iso = datetime.now(UTC).isoformat()
        for row in self._records:
            if int(row.get("memory_id", 0)) != memory_id:
                continue
            row["updated_at"] = now_iso
            row["importance_score"] = float(row.get("importance_score", 0.5)) + float(importance_delta)
            break
        self._write_json(self.index_file, self._records)

    async def store_command(self, *, session_id: str, agent_id: str, command: str, result: dict[str, Any], success: bool, **kwargs: Any) -> None:
        normalized_session_id = await self.upsert_session(session_id, agent_id=agent_id)
        self._write_json(
            self.storage_dir / "commands" / f"{normalized_session_id}_{agent_id}_{datetime.now().timestamp()}.json",
            {
                "session_id": normalized_session_id,
                "source_session_id": session_id,
                "agent_id": agent_id,
                "command": command,
                "result": result,
                "success": success,
                "tokens_used": kwargs.get("tokens_used"),
                "executed_at": datetime.now(UTC).isoformat(),
            },
        )

    async def list_recent_commands(self, *, session_id: str, agent_id: str, limit: int = 12) -> list[dict[str, Any]]:
        normalized_session_id = await self.upsert_session(session_id, agent_id=agent_id)
        rows: list[dict[str, Any]] = []
        for path in self.storage_dir.joinpath("commands").glob("*.json"):
            row = self._read_json(path, default={})
            if row.get("session_id") != normalized_session_id:
                continue
            if row.get("agent_id") != agent_id:
                continue
            rows.append(row)
        rows.sort(key=lambda row: str(row.get("executed_at", "")), reverse=True)
        return rows[: max(1, int(limit))]

    async def flush_all(self) -> int:
        return 0

    def consolidate_episodic(self, *, session_id: str, agent_id: str, chunk_size: int = 5) -> str | None:
        """Stub for episodic memory consolidation."""
        _ = (session_id, agent_id, chunk_size)
        return "Consolidation placeholder"

    @staticmethod
    def serialize_payload(payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=True, default=str)

    @staticmethod
    def _read_json(path: Path, *, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=True, default=str), encoding="utf-8")

    def _index_record(self, row: dict[str, Any], idx: int) -> None:
        session_id = str(row.get("session_id", ""))
        agent_id = str(row.get("agent_id", ""))
        memory_type = str(row.get("memory_type", ""))
        sat = (session_id, agent_id, memory_type)
        self._by_sat.setdefault(sat, []).append(idx)

        meta = row.get("metadata") or {}
        key = str(meta.get("key", "")).strip()
        if key:
            satk = (session_id, agent_id, memory_type, key)
            self._by_satk.setdefault(satk, []).append(idx)
