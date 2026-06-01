from __future__ import annotations
import os
class TemporalBackend:
    def __init__(self) -> None:
        self.enabled = os.getenv("AI_BRIDGE_ENABLE_TEMPORAL", "false").lower() in {"1","true","yes","on"}
    def run(self, payload: dict[str, object]) -> dict[str, object]:
        return {"enabled": self.enabled, "backend": "temporal", "payload": payload}
