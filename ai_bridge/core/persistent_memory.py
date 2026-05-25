from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from .memory_settings import MemorySettings

logger = logging.getLogger(__name__)

try:
    from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, Text, text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
except Exception:  # pragma: no cover
    AsyncSession = Any  # type: ignore[assignment]
    async_sessionmaker = None  # type: ignore[assignment]
    create_async_engine = None  # type: ignore[assignment]
    DeclarativeBase = object  # type: ignore[assignment]
    Mapped = Any  # type: ignore[assignment]
    mapped_column = None  # type: ignore[assignment]
    JSON = Boolean = DateTime = Float = Integer = Text = text = None  # type: ignore[assignment]


class Base(DeclarativeBase):
    pass


if mapped_column is not None:
    class MemoryRow(Base):
        __tablename__ = "memories"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        session_id: Mapped[str] = mapped_column(Text, nullable=False)
        agent_id: Mapped[str] = mapped_column(Text, nullable=False)
        memory_type: Mapped[str] = mapped_column(Text, nullable=False)
        content: Mapped[str] = mapped_column(Text, nullable=False)
        importance_score: Mapped[float] = mapped_column(Float, default=1.0)
        access_count: Mapped[int] = mapped_column(Integer, default=0)
        last_accessed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
        metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
        expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


@dataclass(slots=True)
class PersistentMemoryRecord:
    memory_id: int
    session_id: str
    agent_id: str
    memory_type: str
    content: str
    importance_score: float = 1.0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    expires_at: datetime | None = None


class PersistentMemoryManager:
    def __init__(self, settings: MemorySettings | None = None) -> None:
        self.settings = settings or MemorySettings.from_env()
        self._records: list[PersistentMemoryRecord] = []
        self._commands: list[dict[str, Any]] = []
        self._next_id = 1
        self._lock = asyncio.Lock()
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

        if self.settings.enabled and self.settings.database_url and create_async_engine and async_sessionmaker:
            try:
                engine = create_async_engine(self.settings.database_url, pool_pre_ping=True)
                self._session_maker = async_sessionmaker(engine, expire_on_commit=False)
            except Exception:
                logger.exception("Failed to initialize SQLAlchemy engine; fallback to in-process store")

    async def upsert_agent(self, agent_id: str, *, agent_type: str = "main", parent_agent_id: str | None = None) -> None:
        _ = (agent_id, agent_type, parent_agent_id)

    async def upsert_session(self, session_id: str, *, agent_id: str, user_id: str | None = None, thread_id: str | None = None, metadata: dict[str, Any] | None = None) -> str:
        _ = (agent_id, user_id, thread_id, metadata)
        try:
            UUID(session_id)
            return session_id
        except Exception:
            return str(uuid4())

    async def store_memory(self, *, session_id: str, agent_id: str, memory_type: str, content: str, importance_score: float = 1.0, metadata: dict[str, Any] | None = None, expires_at: datetime | None = None) -> int:
        if self._session_maker is not None and mapped_column is not None:
            async with self._session_maker() as session:
                async with session.begin():
                    row = MemoryRow(
                        session_id=session_id,
                        agent_id=agent_id,
                        memory_type=memory_type,
                        content=content,
                        importance_score=max(0.0, min(1.0, importance_score)),
                        metadata_json=metadata or {},
                        expires_at=expires_at,
                    )
                    session.add(row)
                await session.refresh(row)
                return int(row.id)

        async with self._lock:
            record = PersistentMemoryRecord(
                memory_id=self._next_id,
                session_id=session_id,
                agent_id=agent_id,
                memory_type=memory_type,
                content=content,
                importance_score=max(0.0, min(1.0, importance_score)),
                metadata=metadata or {},
                expires_at=expires_at,
            )
            self._records.append(record)
            self._next_id += 1
            return record.memory_id

    async def store_command(self, *, session_id: str, agent_id: str, command: str, result: dict[str, Any], success: bool, tokens_used: int | None = None) -> None:
        if self._session_maker is not None:
            async with self._session_maker() as session:
                async with session.begin():
                    await session.execute(
                        text(
                            """
                            INSERT INTO command_history (session_id, agent_id, command, result, success, tokens_used)
                            VALUES (:session_id, :agent_id, :command, CAST(:result AS jsonb), :success, :tokens_used)
                            """
                        ),
                        {
                            "session_id": session_id,
                            "agent_id": agent_id,
                            "command": command,
                            "result": json.dumps(result, ensure_ascii=True),
                            "success": success,
                            "tokens_used": tokens_used,
                        },
                    )
            return

        async with self._lock:
            self._commands.append({"session_id": session_id, "agent_id": agent_id, "command": command, "result": result, "success": success, "tokens_used": tokens_used, "executed_at": datetime.now(UTC)})

    async def retrieve_memories(self, *, session_id: str, agent_id: str, memory_type: str | None = None, top_k: int = 8, query_embedding: list[float] | None = None) -> list[PersistentMemoryRecord]:
        if self._session_maker is not None and mapped_column is not None:
            async with self._session_maker() as session:
                params: dict[str, Any] = {"session_id": session_id, "agent_id": agent_id, "limit": max(1, top_k)}
                
                if query_embedding:
                    vec_str = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"
                    params["query_embedding"] = vec_str
                    query = """
                        SELECT id, session_id, agent_id, memory_type, content, importance_score, access_count, last_accessed, created_at, metadata, expires_at,
                               1 - (embedding <=> :query_embedding::vector) AS similarity
                        FROM memories
                        WHERE session_id = :session_id AND agent_id = :agent_id
                    """
                else:
                    query = """
                        SELECT id, session_id, agent_id, memory_type, content, importance_score, access_count, last_accessed, created_at, metadata, expires_at
                        FROM memories
                        WHERE session_id = :session_id AND agent_id = :agent_id
                    """
                
                if memory_type:
                    query += " AND memory_type = :memory_type"
                    params["memory_type"] = memory_type
                
                if query_embedding:
                    query += " ORDER BY (importance_score * 0.3) + (similarity * 0.7) DESC, last_accessed DESC LIMIT :limit"
                else:
                    query += " ORDER BY importance_score DESC, last_accessed DESC LIMIT :limit"
                    
                rows = (await session.execute(text(query), params)).mappings().all()
                return [
                    PersistentMemoryRecord(
                        memory_id=int(r["id"]),
                        session_id=str(r["session_id"]),
                        agent_id=str(r["agent_id"]),
                        memory_type=str(r["memory_type"]),
                        content=str(r["content"]),
                        importance_score=float(r["importance_score"]),
                        access_count=int(r["access_count"]),
                        last_accessed=r["last_accessed"],
                        created_at=r["created_at"],
                        metadata=dict(r["metadata"] or {}),
                        expires_at=r["expires_at"],
                    )
                    for r in rows
                ]

        now = datetime.now(UTC)
        async with self._lock:
            filtered = [
                r
                for r in self._records
                if r.session_id == session_id and r.agent_id == agent_id and (memory_type is None or r.memory_type == memory_type) and (r.expires_at is None or r.expires_at > now)
            ]
            filtered.sort(key=lambda r: (r.importance_score, r.last_accessed), reverse=True)
            return filtered[: max(1, top_k)]

    async def touch_memory(self, memory_id: int, *, importance_delta: float = 0.0) -> None:
        if self._session_maker is not None:
            async with self._session_maker() as session:
                async with session.begin():
                    await session.execute(
                        text(
                            """
                            UPDATE memories
                            SET access_count = access_count + 1,
                                last_accessed = NOW(),
                                importance_score = LEAST(1.0, GREATEST(0.0, importance_score + :importance_delta))
                            WHERE id = :memory_id
                            """
                        ),
                        {"memory_id": memory_id, "importance_delta": importance_delta},
                    )
            return

        async with self._lock:
            for record in self._records:
                if record.memory_id == memory_id:
                    record.access_count += 1
                    record.last_accessed = datetime.now(UTC)
                    record.importance_score = max(0.0, min(1.0, record.importance_score + importance_delta))
                    break

    async def list_recent_commands(self, *, session_id: str, agent_id: str, limit: int = 12) -> list[dict[str, Any]]:
        if self._session_maker is not None:
            async with self._session_maker() as session:
                rows = (
                    await session.execute(
                        text(
                            """
                            SELECT command, result, success, tokens_used, executed_at
                            FROM command_history
                            WHERE session_id = :session_id AND agent_id = :agent_id
                            ORDER BY executed_at DESC
                            LIMIT :limit
                            """
                        ),
                        {"session_id": session_id, "agent_id": agent_id, "limit": max(1, limit)},
                    )
                ).mappings().all()
                return [dict(row) for row in rows][::-1]

        async with self._lock:
            items = [c for c in self._commands if c["session_id"] == session_id and c["agent_id"] == agent_id]
            return items[-max(1, limit) :]

    async def consolidate_episodic(self, *, session_id: str, agent_id: str, chunk_size: int = 5) -> str | None:
        rows = await self.retrieve_memories(session_id=session_id, agent_id=agent_id, memory_type="episodic", top_k=100)
        if len(rows) < chunk_size:
            return None
        snippet = "\n".join(r.content[:180] for r in rows[-chunk_size:])
        summary = f"Consolidated summary ({len(rows[-chunk_size:])} episodes):\n{snippet}"
        await self.store_memory(session_id=session_id, agent_id=agent_id, memory_type="summary", content=summary, importance_score=0.8, metadata={"generated_by": "memory_consolidator"})
        return summary

    @staticmethod
    def serialize_payload(payload: Any) -> str:
        try:
            return json.dumps(payload, ensure_ascii=True, default=str)
        except TypeError:
            logger.exception("Failed to serialize payload for persistence")
            return str(payload)
