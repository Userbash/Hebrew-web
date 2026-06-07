from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .memory_backend import BackendEntry, InMemoryBackend, MemoryBackend
from .memory_settings import MemorySettings
from .persistent_memory import PersistentMemoryManager

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MemoryStub:
    memory_id: int | None
    summary: str
    persisted: bool


@dataclass(slots=True)
class HotEntry:
    key: str
    value: Any
    scope: str
    identifier: str
    created_at: datetime
    last_accessed: datetime
    expires_at: datetime | None
    importance_score: float = 0.5
    access_count: int = 0
    memory_type: str = "episodic"
    tags: list[str] = field(default_factory=list)
    indexed_terms: set[str] = field(default_factory=set)
    stub: MemoryStub | None = None
    vfs_warm: bool = False


@dataclass(slots=True)
class RetrievalHit:
    key: str
    value: Any
    score: float
    semantic_similarity: float
    importance_score: float
    time_decay: float


class HybridMemory:
    def __init__(self, settings: MemorySettings | None = None, backend: MemoryBackend | None = None, persistent: PersistentMemoryManager | None = None) -> None:
        self.settings = settings or MemorySettings.from_env()
        self.backend = backend or InMemoryBackend()
        self.persistent = persistent or PersistentMemoryManager(self.settings)
        self._hot: dict[str, HotEntry] = {}
        self._term_index: dict[str, set[str]] = {}
        self._session_index: dict[str, set[str]] = {}
        self._project_index: dict[str, set[str]] = {}
        self._maintenance_task: asyncio.Task[None] | None = None

    @staticmethod
    def make_key(scope: str, identifier: str, key: str) -> str:
        return f"{scope}:{identifier}:{key}"

    @staticmethod
    def session_state_key(session_id: str) -> str:
        return f"session:{session_id}:state"

    @staticmethod
    def session_env_key(session_id: str) -> str:
        return f"session:{session_id}:context:env"

    @staticmethod
    def session_agent_thoughts_key(session_id: str, agent_id: str) -> str:
        return f"session:{session_id}:agent:{agent_id}:thoughts"

    @staticmethod
    def session_agent_errors_key(session_id: str, agent_id: str) -> str:
        return f"session:{session_id}:agent:{agent_id}:errors"

    @staticmethod
    def domain_patterns_key(project_name: str) -> str:
        return f"memory:domain:{project_name}:patterns"

    @staticmethod
    def capability_practices_key(capability: str) -> str:
        return f"memory:capability:{capability}:best_practices"

    @staticmethod
    def task_artifacts_diff_key(task_id: str) -> str:
        return f"task:{task_id}:artifacts:diff"

    @staticmethod
    def task_metrics_perf_key(task_id: str) -> str:
        return f"task:{task_id}:metrics:perf"

    def get(self, scope: str, identifier: str, key: str) -> Any | None:
        skey = self.make_key(scope, identifier, key)
        entry = self._hot.get(skey)
        if entry:
            if entry.expires_at and datetime.now(UTC) >= entry.expires_at:
                self._drop_key(skey)
                return None
            entry.access_count += 1
            entry.last_accessed = datetime.now(UTC)
            backend_entry = self.backend.get(skey)
            return backend_entry.value if backend_entry else entry.value
        return self._restore_from_persistent(scope, identifier, key)

    def set(self, scope: str, identifier: str, key: str, value: Any, *, expires_at: datetime | None = None, importance_score: float = 0.5, memory_type: str = "episodic", tags: list[str] | None = None) -> None:
        now = datetime.now(UTC)
        skey = self.make_key(scope, identifier, key)
        if skey in self._hot:
            self._remove_indexes(skey, self._hot[skey])

        terms = self._entry_terms(skey, value)
        self._hot[skey] = HotEntry(
            key=key,
            value=value,
            scope=scope,
            identifier=identifier,
            created_at=now,
            last_accessed=now,
            expires_at=expires_at,
            importance_score=max(0.0, min(1.0, importance_score)),
            memory_type=memory_type,
            tags=tags or [],
            indexed_terms=terms,
        )
        self.backend.set(skey, BackendEntry(value=value, created_at=now, expires_at=expires_at, last_accessed_at=now))
        self._add_indexes(skey, self._hot[skey])
        if len(self._hot) > self.settings.hot_cache_max_entries:
            self.run_maintenance_once()

    def get_by_full_key(self, full_key: str) -> Any | None:
        entry = self._hot.get(full_key)
        if entry:
            return entry.value
        backend_entry = self.backend.get(full_key)
        return backend_entry.value if backend_entry else None

    def set_by_full_key(self, full_key: str, value: Any, *, expires_at: datetime | None = None, importance_score: float = 0.5, memory_type: str = "episodic", tags: list[str] | None = None) -> None:
        now = datetime.now(UTC)
        chunks = full_key.split(":")
        scope = chunks[0] if chunks else "global"
        identifier = chunks[1] if len(chunks) > 1 else "default"
        key = ":".join(chunks[2:]) if len(chunks) > 2 else full_key
        if full_key in self._hot:
            self._remove_indexes(full_key, self._hot[full_key])

        terms = self._entry_terms(full_key, value)
        self._hot[full_key] = HotEntry(
            key=key,
            value=value,
            scope=scope,
            identifier=identifier,
            created_at=now,
            last_accessed=now,
            expires_at=expires_at,
            importance_score=max(0.0, min(1.0, importance_score)),
            memory_type=memory_type,
            tags=tags or [],
            indexed_terms=terms,
        )
        self.backend.set(full_key, BackendEntry(value=value, created_at=now, expires_at=expires_at, last_accessed_at=now))
        self._add_indexes(full_key, self._hot[full_key])

    def append_agent_thought(self, *, session_id: str, agent_id: str, thought: str) -> None:
        key = self.session_agent_thoughts_key(session_id, agent_id)
        thoughts = self.get_by_full_key(key) or []
        if not isinstance(thoughts, list):
            thoughts = [str(thoughts)]
        thoughts.append(thought)
        self.set_by_full_key(key, thoughts, importance_score=0.4, memory_type="thought")

    def append_agent_error(self, *, session_id: str, agent_id: str, error: str) -> None:
        key = self.session_agent_errors_key(session_id, agent_id)
        errors = self.get_by_full_key(key) or []
        if not isinstance(errors, list):
            errors = [str(errors)]
        errors.append(error)
        self.set_by_full_key(key, errors, importance_score=0.8, memory_type="error")

    def clear_session_thoughts(self, *, session_id: str) -> int:
        prefix = f"session:{session_id}:agent:"
        removed = 0
        for key in list(self._hot.keys()):
            if key.startswith(prefix) and (key.endswith(":thoughts") or key.endswith(":errors")):
                self._drop_key(key)
                removed += 1
        return removed

    def fast_retrieve(
        self,
        *,
        query_text: str,
        session_id: str | None = None,
        project_name: str | None = None,
        top_k: int = 3,
        api: Any | None = None,
    ) -> list[RetrievalHit]:
        now = datetime.now(UTC)
        hits: list[RetrievalHit] = []

        # 1. Semantic Search (Vector) if LLM is available
        query_vector: list[float] = []
        if api:
            local_llm = api.get_module("local_llm")
            if local_llm and getattr(local_llm, "ready", False):
                try:
                    # In a real system, we'd use a dedicated embedding endpoint.
                    # Here we use the LLM to get a representation or just tokens.
                    # For prototype, we'll keep using the token-based fallback but with higher weights.
                    pass
                except Exception:
                    pass

        norm_query_terms = set(self._tokenize(query_text))
        candidate_keys = self._candidate_keys(norm_query_terms, session_id=session_id, project_name=project_name)
        
        for full_key in candidate_keys:
            entry = self._hot.get(full_key)
            if not entry:
                continue
            
            semantic_similarity = self._semantic_similarity(norm_query_terms, list(entry.indexed_terms))
            age_sec = max(1.0, (now - entry.last_accessed).total_seconds())
            
            # Time Decay: Newer is better (Half-life: 1 hour)
            time_decay = 1.0 / (1.0 + age_sec / 3600.0)
            
            # Weighted Scoring: Semantic (50%) + Importance (30%) + Recency (20%)
            score = 0.5 * semantic_similarity + 0.3 * entry.importance_score + 0.2 * time_decay
            
            hits.append(
                RetrievalHit(
                    key=full_key,
                    value=entry.value,
                    score=score,
                    semantic_similarity=semantic_similarity,
                    importance_score=entry.importance_score,
                    time_decay=time_decay,
                )
            )

        hits.sort(key=lambda x: x.score, reverse=True)
        return hits[: max(1, top_k)]

    def build_context_brief(self, *, hits: list[RetrievalHit], token_limit: int = 1500) -> str:
        """Compresses retrieved memory into a surgically precise context brief."""
        budget_chars = max(200, token_limit * 4)
        lines: list[str] = [f"--- RELEVANT MEMORY (Top {len(hits)}) ---"]
        used = len(lines[0])
        
        for hit in hits:
            # Format: [Score: 0.85] [Scope: session] key: content...
            score_tag = f"[Relevance: {hit.score:.2f}]"
            content = str(hit.value)
            if len(content) > 500:
                content = content[:497] + "..."
            
            line = f"{score_tag} {hit.key}: {content}"
            if used + len(line) + 1 > budget_chars:
                break
            lines.append(line)
            used += len(line) + 1
            
        return "\n".join(lines)

    def delete(self, scope: str, identifier: str, key: str) -> None:
        skey = self.make_key(scope, identifier, key)
        self._drop_key(skey)

    def list_keys(self) -> list[str]:
        return list(self._hot.keys())

    def invalidate(self, prefix: str | None = None) -> int:
        removed = 0
        for skey in list(self._hot.keys()):
            if prefix and not skey.startswith(prefix):
                continue
            self._drop_key(skey)
            removed += 1
        return removed

    def clear(self) -> None:
        self._hot.clear()
        self._term_index.clear()
        self._session_index.clear()
        self._project_index.clear()
        self.backend.clear()

    def soft_flush(self, api: Any | None = None) -> int:
        """Persist all hot entries and buffered records with AI-driven compaction."""
        flushed = 0
        local_llm = api.get_module("local_llm") if api else None
        
        # Batch events for compaction if many
        if len(self._hot) > 10 and local_llm and getattr(local_llm, "ready", False):
            try:
                # Group by session for compaction
                raw_logs = [{"key": entry.key, "value": str(entry.value)} for entry in self._hot.values()]
                summary = local_llm.compact_memory(raw_logs)
                # Store summary as a special 'Anchor' memory
                self.set("session", "system", "archive_summary", summary, importance_score=0.9, memory_type="anchor")
            except Exception:
                pass

        for _, entry in list(self._hot.items()):
            # Use AI to generate indexing keywords if missing
            if not entry.tags and local_llm and getattr(local_llm, "ready", False):
                entry.tags = local_llm.generate_embedding_keywords(str(entry.value))

            memory_id = self.persistent.store_memory(
                session_id=entry.identifier,
                agent_id=self._persistence_agent_id(entry.scope, entry.identifier),
                memory_type=entry.memory_type,
                content=self.persistent.serialize_payload(entry.value),
                importance_score=entry.importance_score,
                metadata={"key": entry.key, "scope": entry.scope, "tags": entry.tags, "vfs_warm": entry.vfs_warm},
                expires_at=entry.expires_at,
            )
            if memory_id:
                entry.stub = MemoryStub(memory_id=memory_id, summary=str(entry.value)[:200], persisted=True)
                flushed += 1

        if hasattr(self.persistent, "flush_all"):
            flushed += self.persistent.flush_all()

        logger.info(f"[MEMORY] Soft flush complete: {flushed} total records persisted.")
        return flushed

    def run_maintenance_once(self) -> int:
        if not self._hot:
            return 0
        now = datetime.now(UTC)
        ranked: list[tuple[float, str, HotEntry]] = []
        for skey, entry in self._hot.items():
            age_sec = max(1.0, (now - entry.created_at).total_seconds())
            idle_sec = max(1.0, (now - entry.last_accessed).total_seconds())
            recency = 1.0 / idle_sec
            access_freq = entry.access_count / age_sec
            score = 0.4 * recency + 0.3 * access_freq + 0.3 * entry.importance_score
            ranked.append((score, skey, entry))
        ranked.sort(key=lambda item: item[0])
        limit = max(1, len(ranked) // 5)
        evicted = 0
        for _, skey, entry in ranked[:limit]:
            memory_id = self._persist_entry(entry)
            entry.stub = MemoryStub(memory_id=memory_id, summary=str(entry.value)[:200], persisted=memory_id is not None)
            self._drop_key(skey)
            evicted += 1
        return evicted

    def start_background_tasks(self) -> None:
        if self._maintenance_task and not self._maintenance_task.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._maintenance_task = loop.create_task(self._maintenance_loop())

    async def _maintenance_loop(self) -> None:
        while True:
            await asyncio.sleep(max(10, self.settings.eviction_interval_sec))
            self.run_maintenance_once()

    def remember_command(self, *, session_id: str, agent_id: str, command: str, result: dict[str, Any], success: bool, tokens_used: int | None = None) -> None:
        self.persistent.store_command(
            session_id=session_id,
            agent_id=agent_id,
            command=command,
            result=result,
            success=success,
            tokens_used=tokens_used,
        )

    def load_command_window(self, *, session_id: str, agent_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        return self.persistent.list_recent_commands(
            session_id=session_id,
            agent_id=agent_id,
            limit=limit or self.settings.command_window_size,
        )

    def get_command_history(self, *, session_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        return self.persistent.list_recent_commands_by_session(
            session_id=session_id,
            limit=limit or self.settings.command_window_size,
        )

    def _persistence_agent_id(self, scope: str, identifier: str) -> str:
        if scope == "agent":
            return identifier
        return f"{scope}-memory"

    def _persist_entry(self, entry: HotEntry) -> int | None:
        persistence_agent_id = self._persistence_agent_id(entry.scope, entry.identifier)
        return self.persistent.store_memory(
            session_id=entry.identifier,
            agent_id=persistence_agent_id,
            memory_type=entry.memory_type,
            content=self.persistent.serialize_payload(entry.value),
            importance_score=entry.importance_score,
            metadata={"key": entry.key, "scope": entry.scope, "tags": entry.tags},
            expires_at=entry.expires_at,
        )

    def _restore_from_persistent(self, scope: str, identifier: str, key: str) -> Any | None:
        persistence_agent_id = self._persistence_agent_id(scope, identifier)
        row = self.persistent.retrieve_memory_by_key(
            session_id=identifier,
            agent_id=persistence_agent_id,
            memory_type="episodic",
            key=key,
        )
        if row is None:
            return None
        self.persistent.touch_memory(row.memory_id, importance_delta=0.01)
        return row.content

    def _candidate_keys(self, query_terms: set[str], *, session_id: str | None, project_name: str | None) -> set[str]:
        candidates: set[str] = set()
        for term in query_terms:
            candidates.update(self._term_index.get(term, set()))

        if not candidates:
            candidates = set(self._hot.keys())

        if session_id:
            candidates &= self._session_index.get(session_id, set())

        if project_name:
            candidates &= self._project_index.get(project_name, set())

        return candidates

    def _add_indexes(self, full_key: str, entry: HotEntry) -> None:
        for term in entry.indexed_terms:
            self._term_index.setdefault(term, set()).add(full_key)

        if entry.scope == "session":
            self._session_index.setdefault(entry.identifier, set()).add(full_key)

        project = self._project_from_key(full_key)
        if project:
            self._project_index.setdefault(project, set()).add(full_key)

    def _remove_indexes(self, full_key: str, entry: HotEntry) -> None:
        for term in entry.indexed_terms:
            bucket = self._term_index.get(term)
            if not bucket:
                continue
            bucket.discard(full_key)
            if not bucket:
                self._term_index.pop(term, None)

        if entry.scope == "session":
            sess_bucket = self._session_index.get(entry.identifier)
            if sess_bucket:
                sess_bucket.discard(full_key)
                if not sess_bucket:
                    self._session_index.pop(entry.identifier, None)

        project = self._project_from_key(full_key)
        if project:
            prj_bucket = self._project_index.get(project)
            if prj_bucket:
                prj_bucket.discard(full_key)
                if not prj_bucket:
                    self._project_index.pop(project, None)

    def _drop_key(self, full_key: str) -> None:
        entry = self._hot.pop(full_key, None)
        if entry:
            self._remove_indexes(full_key, entry)
        self.backend.delete(full_key)

    @staticmethod
    def _project_from_key(full_key: str) -> str | None:
        parts = full_key.split(":")
        if len(parts) >= 4 and parts[0] == "memory" and parts[1] == "domain":
            return parts[2]
        return None

    def _entry_terms(self, full_key: str, value: Any) -> set[str]:
        tokens = self._tokenize(full_key)
        tokens.extend(self._tokenize(str(value)[:1024]))
        return set(tokens)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        normalized = text.lower().replace("\n", " ").replace(":", " ").replace("_", " ").replace("-", " ")
        return [part for part in normalized.split(" ") if part]

    @staticmethod
    def _semantic_similarity(query_terms: set[str], candidate_terms: list[str]) -> float:
        if not query_terms or not candidate_terms:
            return 0.0
        cset = set(candidate_terms)
        intersection = len(query_terms.intersection(cset))
        union = max(1, len(query_terms.union(cset)))
        return intersection / union
