from __future__ import annotations
import os
class LiteLLMProviderAdapter:
    def __init__(self) -> None:
        self.enabled = os.getenv("AI_BRIDGE_ENABLE_LITELLM", "false").lower() in {"1","true","yes","on"}
    def complete(self, prompt: str, **kwargs):
        return {"enabled": self.enabled, "prompt": prompt, "kwargs": kwargs, "provider": "litellm"}
