from __future__ import annotations
from typing import Protocol, Any
class ContextManager(Protocol):
    def build_context(self, task: Any, memory_refs: list[str] | None = None) -> dict[str, Any]: ...
