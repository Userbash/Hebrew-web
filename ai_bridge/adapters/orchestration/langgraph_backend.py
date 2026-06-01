from __future__ import annotations
import os
class LangGraphBackend:
    def __init__(self) -> None:
        self.enabled = os.getenv("AI_BRIDGE_ENABLE_LANGGRAPH", "false").lower() in {"1","true","yes","on"}
    def run(self, payload: dict[str, object]) -> dict[str, object]:
        return {"enabled": self.enabled, "backend": "langgraph", "payload": payload}
