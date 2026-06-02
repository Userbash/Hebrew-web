from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict

from pydantic import BaseModel, Field
from .kernel_protocol import KernelAPI, KernelModule

logger = logging.getLogger("intent_analyzer_module")

class DesignSchema(BaseModel):
    layout: str = Field(..., description="The type of layout, e.g., 'bento-grid', 'sidebar', 'landing'")
    primary_color: str = Field(..., description="Primary hex color code")
    components: list[str] = Field(..., description="List of UI components to include")
    vibe: str = Field(..., description="The stylistic vibe, e.g., 'minimalist', 'brutalist', 'corporate'")

@dataclass
class IntentAnalyzerModule(KernelModule):
    name: str = "intent_analyzer"
    _api: KernelAPI | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", f"[UI] {self.name} module loaded")

    def analyze_user_prompt(self, prompt: str) -> DesignSchema:
        """
        Interprets user prompt and returns a structured DesignSchema based on intent.
        """
        self._api.log("info", f"[UI] Analyzing prompt: {prompt}")
        
        prompt_lower = prompt.lower()
        
        # Language School Design System Logic
        if "language school" in prompt_lower:
            simulated_response = {
                "layout": "bento-grid",
                "primary_color": "#2A5C82",
                "components": ["HeroSection", "FeatureCards", "UserTable"],
                "vibe": "minimalist"
            }
        else:
            # Default fallback
            simulated_response = {
                "layout": "landing",
                "primary_color": "#000000",
                "components": ["HeroSection", "FeatureCards"],
                "vibe": "minimalist"
            }
        
        return DesignSchema(**simulated_response)

    def on_unload(self) -> None:
        if self._api:
            self._api.log("info", f"[UI] {self.name} module unloaded")

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        pass

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        pass

    def finalize(self) -> dict[str, Any]:
        return {"status": "active"}
