from __future__ import annotations
from typing import Protocol, Any
class OrchestrationBackend(Protocol):
    def run(self, payload: dict[str, Any]) -> dict[str, Any]: ...
