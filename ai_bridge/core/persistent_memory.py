from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

AI_BRIDGE_SCHEMA = "ai_bridge"


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


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+asyncpg://")
    if database_url.startswith("postgresql+psycopg2://"):
        return "postgresql://" + database_url.removeprefix("postgresql+psycopg2://")
    return database_url


def normalize_session_id(session_id: str) -> str:
    return f"sess-{hashlib.sha256(session_id.encode('utf-8')).hexdigest()[:16]}"


def ensure_storage_schema(database_url: str) -> bool:
    dsn = normalize_database_url(database_url.strip())
    if not dsn:
        return False

    try:
        import psycopg2  # type: ignore
    except Exception as exc:
        logger.warning("[MEMORY] psycopg2 unavailable, PostgreSQL memory disabled: %s", exc)
        return False

    statements = [
        f"CREATE SCHEMA IF NOT EXISTS {AI_BRIDGE_SCHEMA}",
        f"""
        CREATE TABLE IF NOT EXISTS {AI_BRIDGE_SCHEMA}.sessions (
            source_session_id TEXT PRIMARY KEY,
            normalized_session_id TEXT NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS {AI_BRIDGE_SCHEMA}.memories (
            memory_id BIGSERIAL PRIMARY KEY,
            session_id TEXT NOT NULL,
            source_session_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            content JSONB NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            importance_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS {AI_BRIDGE_SCHEMA}.commands (
            command_id BIGSERIAL PRIMARY KEY,
            session_id TEXT NOT NULL,
            source_session_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            command TEXT NOT NULL,
            result JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            success BOOLEAN NOT NULL DEFAULT FALSE,
            tokens_used BIGINT,
            executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS {AI_BRIDGE_SCHEMA}.json_themes (
            theme_event_id BIGSERIAL PRIMARY KEY,
            task_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            agent_id TEXT,
            provider TEXT,
            color TEXT,
            status TEXT,
            event_payload JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        f"CREATE INDEX IF NOT EXISTS idx_ai_bridge_memories_lookup ON {AI_BRIDGE_SCHEMA}.memories (session_id, agent_id, memory_type, memory_id DESC)",
        f"CREATE INDEX IF NOT EXISTS idx_ai_bridge_memories_key ON {AI_BRIDGE_SCHEMA}.memories (session_id, agent_id, memory_type, ((metadata->>'key')), memory_id DESC)",
        f"CREATE INDEX IF NOT EXISTS idx_ai_bridge_commands_lookup ON {AI_BRIDGE_SCHEMA}.commands (session_id, agent_id, executed_at DESC)",
        f"CREATE INDEX IF NOT EXISTS idx_ai_bridge_themes_lookup ON {AI_BRIDGE_SCHEMA}.json_themes (session_id, created_at DESC)",
    ]

    conn = None
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        with conn.cursor() as cur:
            for statement in statements:
                cur.execute(statement)
        return True
    except Exception as exc:
        logger.warning("[MEMORY] PostgreSQL schema initialization failed: %s", exc)
        return False
    finally:
        if conn is not None:
            conn.close()


class PersistentMemoryManager:
    """Persistent memory backed by isolated PostgreSQL schema, with file fallback."""

    def __init__(self, settings: Any = None) -> None:
        self.settings = settings
        self.database_url = str(getattr(settings, "database_url", "") or os.getenv("AI_BRIDGE_MEMORY_DATABASE_URL", "")).strip()
        self._pg_enabled = bool(self.database_url and ensure_storage_schema(self.database_url))

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

        mode = "PostgreSQL" if self._pg_enabled else "file"
        logger.info("[MEMORY] Operating in %s mode.", mode)

    def _connect(self):
        import psycopg2  # type: ignore

        return psycopg2.connect(normalize_database_url(self.database_url))

    def upsert_session(self, session_id: str, *, agent_id: str) -> str:
        _ = agent_id
        normalized = normalize_session_id(session_id)
        if self._pg_enabled:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {AI_BRIDGE_SCHEMA}.sessions (source_session_id, normalized_session_id, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (source_session_id)
                        DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                        RETURNING normalized_session_id
                        """,
                        (session_id, normalized),
                    )
                    row = cur.fetchone()
                    return str(row[0])

        mapping = self._read_json(self.session_map_file, default={})
        if session_id in mapping:
            return str(mapping[session_id])
        mapping[session_id] = normalized
        self._write_json(self.session_map_file, mapping)
        return normalized

    def store_memory(self, *, session_id: str, agent_id: str, memory_type: str, content: Any, **kwargs: Any) -> int:
        normalized_session_id = self.upsert_session(session_id, agent_id=agent_id)
        metadata = kwargs.get("metadata") or {}
        importance_score = float(kwargs.get("importance_score", 0.5))

        if self._pg_enabled:
            from psycopg2.extras import Json  # type: ignore

            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {AI_BRIDGE_SCHEMA}.memories (
                            session_id, source_session_id, agent_id, memory_type,
                            content, metadata, importance_score
                        )
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
                        RETURNING memory_id
                        """,
                        (normalized_session_id, session_id, agent_id, memory_type, Json(content), Json(metadata), importance_score),
                    )
                    row = cur.fetchone()
                    return int(row[0])

        now_iso = datetime.now(UTC).isoformat()
        memory_id = self._max_memory_id + 1
        record = {
            "memory_id": memory_id,
            "session_id": normalized_session_id,
            "source_session_id": session_id,
            "agent_id": agent_id,
            "memory_type": memory_type,
            "content": content,
            "metadata": metadata,
            "importance_score": importance_score,
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

    def retrieve_memories(self, *, session_id: str, agent_id: str, memory_type: str, top_k: int = 8) -> list[MemoryRecord]:
        normalized_session_id = self.upsert_session(session_id, agent_id=agent_id)
        limit = max(1, int(top_k))
        if self._pg_enabled:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT memory_id, session_id, agent_id, memory_type, content, metadata,
                               importance_score, created_at, updated_at
                        FROM {AI_BRIDGE_SCHEMA}.memories
                        WHERE session_id = %s AND agent_id = %s AND memory_type = %s
                        ORDER BY memory_id DESC
                        LIMIT %s
                        """,
                        (normalized_session_id, agent_id, memory_type, limit),
                    )
                    return [self._record_from_row(row) for row in cur.fetchall()]

        sat = (normalized_session_id, agent_id, memory_type)
        indexes = self._by_sat.get(sat, [])
        filtered = [self._records[idx] for idx in reversed(indexes)]
        return [self._record_from_dict(row) for row in filtered[:limit]]

    def retrieve_memory_by_key(self, *, session_id: str, agent_id: str, memory_type: str, key: str) -> MemoryRecord | None:
        normalized_session_id = self.upsert_session(session_id, agent_id=agent_id)
        if self._pg_enabled:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT memory_id, session_id, agent_id, memory_type, content, metadata,
                               importance_score, created_at, updated_at
                        FROM {AI_BRIDGE_SCHEMA}.memories
                        WHERE session_id = %s
                          AND agent_id = %s
                          AND memory_type = %s
                          AND metadata->>'key' = %s
                        ORDER BY memory_id DESC
                        LIMIT 1
                        """,
                        (normalized_session_id, agent_id, memory_type, key),
                    )
                    row = cur.fetchone()
                    return self._record_from_row(row) if row else None

        satk = (normalized_session_id, agent_id, memory_type, key)
        indexes = self._by_satk.get(satk, [])
        if not indexes:
            return None
        return self._record_from_dict(self._records[indexes[-1]])

    def touch_memory(self, memory_id: int, *, importance_delta: float = 0.0) -> None:
        if self._pg_enabled:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE {AI_BRIDGE_SCHEMA}.memories
                        SET updated_at = CURRENT_TIMESTAMP,
                            importance_score = importance_score + %s
                        WHERE memory_id = %s
                        """,
                        (float(importance_delta), int(memory_id)),
                    )
            return

        now_iso = datetime.now(UTC).isoformat()
        for row in self._records:
            if int(row.get("memory_id", 0)) != memory_id:
                continue
            row["updated_at"] = now_iso
            row["importance_score"] = float(row.get("importance_score", 0.5)) + float(importance_delta)
            break
        self._write_json(self.index_file, self._records)

    def store_command(self, *, session_id: str, agent_id: str, command: str, result: dict[str, Any], success: bool, **kwargs: Any) -> None:
        normalized_session_id = self.upsert_session(session_id, agent_id=agent_id)
        if self._pg_enabled:
            from psycopg2.extras import Json  # type: ignore

            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {AI_BRIDGE_SCHEMA}.commands (
                            session_id, source_session_id, agent_id, command, result, success, tokens_used
                        )
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
                        """,
                        (normalized_session_id, session_id, agent_id, command, Json(result), bool(success), kwargs.get("tokens_used")),
                    )
            return

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

    def list_recent_commands(self, *, session_id: str, agent_id: str, limit: int = 12) -> list[dict[str, Any]]:
        normalized_session_id = self.upsert_session(session_id, agent_id=agent_id)
        bounded_limit = max(1, int(limit))
        if self._pg_enabled:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT session_id, source_session_id, agent_id, command, result, success, tokens_used, executed_at
                        FROM {AI_BRIDGE_SCHEMA}.commands
                        WHERE session_id = %s AND agent_id = %s
                        ORDER BY executed_at DESC
                        LIMIT %s
                        """,
                        (normalized_session_id, agent_id, bounded_limit),
                    )
                    return [self._command_from_row(row) for row in cur.fetchall()]

        rows = []
        for path in self.storage_dir.joinpath("commands").glob("*.json"):
            row = self._read_json(path, default={})
            if row.get("session_id") == normalized_session_id and row.get("agent_id") == agent_id:
                rows.append(row)
        rows.sort(key=lambda row: str(row.get("executed_at", "")), reverse=True)
        return rows[:bounded_limit]

    def list_recent_commands_by_session(self, *, session_id: str, limit: int = 12) -> list[dict[str, Any]]:
        normalized_session_id = self.upsert_session(session_id, agent_id="any")
        bounded_limit = max(1, int(limit))
        if self._pg_enabled:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT session_id, source_session_id, agent_id, command, result, success, tokens_used, executed_at
                        FROM {AI_BRIDGE_SCHEMA}.commands
                        WHERE session_id = %s
                        ORDER BY executed_at DESC
                        LIMIT %s
                        """,
                        (normalized_session_id, bounded_limit),
                    )
                    return [self._command_from_row(row) for row in cur.fetchall()]

        rows = []
        for path in self.storage_dir.joinpath("commands").glob("*.json"):
            row = self._read_json(path, default={})
            if row.get("session_id") == normalized_session_id:
                rows.append(row)
        rows.sort(key=lambda row: str(row.get("executed_at", "")), reverse=True)
        return rows[:bounded_limit]

    def flush_all(self) -> int:
        return 0

    def consolidate_episodic(self, *, session_id: str, agent_id: str, chunk_size: int = 5) -> str | None:
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
        self._by_sat.setdefault((session_id, agent_id, memory_type), []).append(idx)

        meta = row.get("metadata") or {}
        key = str(meta.get("key", "")).strip()
        if key:
            self._by_satk.setdefault((session_id, agent_id, memory_type, key), []).append(idx)

    @staticmethod
    def _record_from_dict(row: dict[str, Any]) -> MemoryRecord:
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

    @staticmethod
    def _record_from_row(row: tuple[Any, ...]) -> MemoryRecord:
        return MemoryRecord(
            memory_id=int(row[0]),
            session_id=str(row[1]),
            agent_id=str(row[2]),
            memory_type=str(row[3]),
            content=row[4],
            metadata=dict(row[5] or {}),
            importance_score=float(row[6]),
            created_at=row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
            updated_at=row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
        )

    @staticmethod
    def _command_from_row(row: tuple[Any, ...]) -> dict[str, Any]:
        executed_at = row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7])
        return {
            "session_id": row[0],
            "source_session_id": row[1],
            "agent_id": row[2],
            "command": row[3],
            "result": row[4],
            "success": row[5],
            "tokens_used": row[6],
            "executed_at": executed_at,
        }
