from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from .kernel_protocol import KernelAPI, KernelModule
from .models import Task, Complexity, Priority

logger = logging.getLogger("risk_advisor")

class RiskAssessment(BaseModel):
    risk_score: float = Field(description="Risk score from 0.0 to 1.0")
    complexity_level: str = Field(description="low, medium, high, critical")
    justification: str
    impact_areas: List[str]
    suggested_review_level: str = Field(description="none, peer, senior, architect")

@dataclass
class RiskAdvisorModule:
    name: str = "risk_advisor"
    _api: KernelAPI | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", f"[RISK] {self.name} module loaded.")

    def on_unload(self) -> None:
        pass

    def evaluate_task(self, task: Task) -> Optional[RiskAssessment]:
        reasoning = self._api.get_module("reasoning") if self._api else None
        if not reasoning or not getattr(reasoning, "_client", None):
            return None

        prompt = f"""Evaluate the risk of the following task:
Task Type: {task.type.value}
Description: {task.input.description}
Files: {', '.join(task.input.files)}
Context: {task.context.repo_path}
"""
        
        system_prompt = "You are a senior security and architecture auditor. Provide a structured risk assessment."
        
        # Use a "Thinking" model if possible, otherwise default.
        model = "gpt-4o" # default reasoning model
        
        return reasoning.structured_call(prompt, RiskAssessment, system_prompt=system_prompt, model=model)

    def finalize(self) -> dict[str, Any]:
        return {"status": "ready"}
