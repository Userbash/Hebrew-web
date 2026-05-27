from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .kernel_api import KernelAPI
from .models import AgentResult, Task

logger = logging.getLogger("model_usage_module")

@dataclass
class ModelStats:
    used_tokens: int = 0
    limit_tokens: int = 1000000  # Default limit per session/day
    requests_count: int = 0
    
    @property
    def remaining_tokens(self) -> int:
        return max(0, self.limit_tokens - self.used_tokens)
        
    @property
    def usage_percentage(self) -> float:
        if self.limit_tokens == 0:
            return 100.0
        return round((self.used_tokens / self.limit_tokens) * 100, 2)

@dataclass(slots=True)
class ModelUsageModule:
    name: str = "model_usage"
    _api: KernelAPI | None = None
    current: dict[str, Any] | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, ModelStats] = field(default_factory=dict)
    
    # Optional: Hardcoded or configurable limits per model
    _model_limits: dict[str, int] = field(default_factory=lambda: {
        "gpt-4": 500000,
        "gpt-coding-large": 800000,
        "gemini-1.5-pro": 1000000,
        "mistral-large-latest": 1500000,
    })

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        if self._api:
            self._api.log("info", f"[{self.name.upper()}] Module loaded. Ready to track token usage.")

    def on_unload(self) -> None:
        if self._api:
            self._api.log("info", f"[{self.name.upper()}] Module unloaded. Tracking stopped.")
        self.current = None

    def _get_or_create_stats(self, model: str) -> ModelStats:
        if model not in self.stats:
            limit = self._model_limits.get(model, 1000000) # Default 1M
            self.stats[model] = ModelStats(limit_tokens=limit)
        return self.stats[model]

    def before_task(self, task: Task, context: dict[str, Any]) -> None:
        model = context.get("model") or context.get("selected_model") or "unknown"
        provider = context.get("provider") or context.get("selected_provider") or "unknown"
        
        self.current = {
            "task_id": task.task_id,
            "task_type": task.type.value,
            "provider": provider,
            "model": model,
            "agent_id": context.get("agent_id"),
            "started_at": datetime.now(UTC).isoformat(),
        }

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None:
        model = context.get("model") or context.get("selected_model") or "unknown"
        provider = context.get("provider") or context.get("selected_provider") or "unknown"
        
        # Simulate token extraction. In a real scenario, this would come from result.metadata 
        # or the LLM provider API response (e.g. usage.total_tokens)
        # We will estimate tokens if not explicitly provided: ~ 4 chars per token.
        input_len = len(str(task.input))
        output_len = len(str(result.output))
        estimated_tokens = (input_len + output_len) // 4
        
        # Override with actual tokens if provider sent them
        actual_tokens = context.get("usage_tokens", estimated_tokens)
        
        # Update Stats
        model_stat = self._get_or_create_stats(model)
        model_stat.used_tokens += actual_tokens
        model_stat.requests_count += 1

        record = {
            "task_id": task.task_id,
            "task_type": task.type.value,
            "provider": provider,
            "model": model,
            "agent_id": context.get("agent_id") or result.agent_id,
            "status": result.status.value,
            "tokens_used": actual_tokens,
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self.history.append(record)
        self.current = None
        
        if self._api:
            self._api.log("info", f"[{self.name.upper()}] {model} used {actual_tokens} tokens. ({model_stat.usage_percentage}% of limit)")

    def get_statistics(self) -> dict[str, Any]:
        """Exposes structured statistics for the API / CLI."""
        summary = {}
        total_used = 0
        
        for model, stat in self.stats.items():
            summary[model] = {
                "used_tokens": stat.used_tokens,
                "limit_tokens": stat.limit_tokens,
                "remaining_tokens": stat.remaining_tokens,
                "usage_percentage": stat.usage_percentage,
                "requests_count": stat.requests_count,
                "status": "warning" if stat.usage_percentage > 80 else ("ok" if stat.usage_percentage > 20 else "low")
            }
            total_used += stat.used_tokens
            
        return {
            "total_tokens_used": total_used,
            "models": summary
        }

    def finalize(self) -> dict[str, Any]:
        return {
            "current": self.current,
            "stats": self.get_statistics()
        }
