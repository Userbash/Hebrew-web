from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from .kernel_protocol import KernelAPI, KernelModule
from .models import Task, AgentResult, Complexity, TaskType

logger = logging.getLogger("ai_intelligence")

class ComplexityAnalysis(BaseModel):
    complexity: str = Field(description="low, medium, high, critical")
    reasoning: str
    estimated_effort_hours: float
    required_capabilities: List[str]

class ErrorDiagnosis(BaseModel):
    error_type: str = Field(description="quota, auth, logic, network, context_overflow, unknown")
    is_retryable: bool
    explanation: str
    suggested_fix: Optional[str]
    recommended_fallback_model: Optional[str]

class MergeStrategy(BaseModel):
    merged_summary: str
    conflicts: List[str]
    integrated_diff: str

@dataclass
class AIIntelligenceModule:
    name: str = "intelligence"
    _api: KernelAPI | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", f"[INTEL] {self.name} module loaded.")

    def on_unload(self) -> None:
        pass

    def estimate_complexity(self, task: Task) -> Optional[ComplexityAnalysis]:
        reasoning = self._api.get_module("reasoning") if self._api else None
        if not reasoning or not getattr(reasoning, "_client", None):
            return None

        prompt = f"""Analyze the complexity of this task:
Type: {task.type.value}
Description: {task.input.description}
Files involved: {len(task.input.files)}
Acceptance Criteria count: {len(task.input.acceptance_criteria)}
"""
        return reasoning.structured_call(prompt, ComplexityAnalysis, system_prompt="You are a technical project manager.", model="gpt-4o")

    def diagnose_error(self, raw_error: str, task: Task, model_used: str) -> Optional[ErrorDiagnosis]:
        # Local LLM is great for classification if ready
        local_llm = self._api.get_module("local_llm") if self._api else None
        if local_llm and getattr(local_llm, "ready", False):
            try:
                prompt = f"""Return JSON only. Diagnose this AI model error:
Error: {raw_error}
Model: {model_used}
Task: {task.input.description[:200]}
Keys: error_type (quota, auth, logic, network, context_overflow, unknown), is_retryable (bool), explanation, suggested_fix, recommended_fallback_model.
"""
                resp = local_llm.query(prompt)
                import json
                return ErrorDiagnosis.model_validate_json(resp)
            except Exception:
                pass

        # Fallback to Cloud Reasoning
        reasoning = self._api.get_module("reasoning") if self._api else None
        if not reasoning or not getattr(reasoning, "_client", None):
            return None

        prompt = f"Diagnose error: {raw_error}\nModel: {model_used}\nTask: {task.input.description[:300]}"
        return reasoning.structured_call(prompt, ErrorDiagnosis, system_prompt="You are an SRE and AI infrastructure expert.")

    def finalize(self) -> dict[str, Any]:
        return {"status": "ready"}
