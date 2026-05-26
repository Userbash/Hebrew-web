from __future__ import annotations

import logging

from .hybrid_memory import HybridMemory

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    def __init__(self, hybrid_memory: HybridMemory) -> None:
        self.hybrid_memory = hybrid_memory

    def consolidate(self, *, session_id: str, agent_id: str) -> str | None:
        try:
            return self.hybrid_memory.persistent.consolidate_episodic(
                session_id=session_id,
                agent_id=agent_id,
                chunk_size=5,
            )
        except Exception:
            logger.exception("Memory consolidation failed")
            return None
