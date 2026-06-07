from __future__ import annotations

import os
from dataclasses import dataclass

from .gemini_model_registry import AntigravityModelRegistry
from .models import Complexity, Task, TaskType


class AntigravityBudgetExhaustedError(RuntimeError):
    pass


@dataclass(slots=True)
class AntigravityRoutingPlan:
    models: list[str]
    estimated_tokens: int
    remaining_tokens: int
    complexity: Complexity
    strategy: str = "balanced"


class AntigravityRuntimeRouter:
    _session_token_usage: dict[str, int] = {}
    _session_blocked_models: dict[str, set[str]] = {}

    def __init__(self) -> None:
        self.session_budget = self._read_int("ANTIGRAVITY_SESSION_TOKEN_BUDGET", os.getenv("GEMINI_SESSION_TOKEN_BUDGET", "200000"))
        self.registry = AntigravityModelRegistry()

    @staticmethod
    def _read_int(key: str, default: int | str) -> int:
        raw = os.getenv(key, str(default)).strip()
        try:
            return int(raw)
        except ValueError:
            return int(default)

    @staticmethod
    def _estimate_prompt_tokens(prompt: str) -> int:
        return max(8, len(prompt) // 4)

    @staticmethod
    def _estimate_completion_tokens(complexity: Complexity) -> int:
        if complexity == Complexity.LOW:
            return 256
        if complexity == Complexity.MEDIUM:
            return 768
        if complexity == Complexity.HIGH:
            return 2048
        return 4096

    def _complexity_ordered_models(self, complexity: Complexity, *, force_refresh: bool = False) -> list[str]:
        catalog = self.registry.get_catalog(force_refresh=force_refresh)
        low = catalog.lite + catalog.flash + catalog.pro + catalog.thinking
        medium = catalog.flash + catalog.pro + catalog.lite + catalog.thinking
        high = catalog.thinking + catalog.pro + catalog.flash + catalog.lite
        low_fb = ["antigravity-flash-lite", "antigravity-flash", "antigravity-pro"]
        med_fb = ["antigravity-flash", "antigravity-flash-lite", "antigravity-pro"]
        high_fb = ["antigravity-pro", "antigravity-flash", "antigravity-flash-lite", "antigravity-thinking"]
        if complexity == Complexity.LOW:
            return low or low_fb
        if complexity == Complexity.MEDIUM:
            return medium or med_fb
        if complexity == Complexity.HIGH:
            return high or high_fb
        return high or high_fb

    @staticmethod
    def _parse_extra_fallbacks() -> list[str]:
        raw = os.getenv("ANTIGRAVITY_CLI_EXTRA_MODELS", os.getenv("GEMINI_CLI_EXTRA_MODELS", "")).strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    @staticmethod
    def strategy_profiles() -> dict[str, list[str]]:
        return {
            "low_cost": ["antigravity-flash-lite", "antigravity-flash"],
            "docs_research": ["antigravity-flash", "antigravity-flash-lite", "antigravity-pro"],
            "code_fix": ["antigravity-flash-lite", "antigravity-flash", "antigravity-pro"],
            "high_reasoning": ["antigravity-thinking", "antigravity-pro", "antigravity-flash"],
        }

    def _strategy_for(self, complexity: Complexity, task: Task) -> str:
        if complexity == Complexity.LOW:
            return "low_cost"
        if complexity == Complexity.MEDIUM and task.type in {TaskType.DOCS, TaskType.RESEARCH, TaskType.REVIEW}:
            return "docs_research"
        if complexity in {Complexity.HIGH, Complexity.CRITICAL}:
            return "high_reasoning"
        if task.type in {TaskType.CODE, TaskType.FIX, TaskType.TEST}:
            return "code_fix"
        return "balanced"

    def build_plan(self, task: Task, prompt: str) -> AntigravityRoutingPlan:
        complexity = task.complexity or Complexity.MEDIUM
        estimated = self._estimate_prompt_tokens(prompt) + self._estimate_completion_tokens(complexity)
        session_id = task.session_id or "default"
        used = self._session_token_usage.get(session_id, 0)
        remaining = max(0, self.session_budget - used)
        strategy = self._strategy_for(complexity, task)

        if remaining <= 0 or estimated > remaining * 2:
            models = ["antigravity-flash-lite", "antigravity-flash"]
            strategy = "low_cost"
        else:
            first_call = used <= 0
            models = self._complexity_ordered_models(complexity, force_refresh=first_call)

        blocked = self._session_blocked_models.get(session_id, set())
        models = [m for m in models if m not in blocked]

        extra = self._parse_extra_fallbacks()
        seen: set[str] = set()
        deduped: list[str] = []
        for model in [*models, *extra]:
            if model in seen:
                continue
            seen.add(model)
            deduped.append(model)

        if not deduped:
            raise AntigravityBudgetExhaustedError("no models available for runtime routing")

        return AntigravityRoutingPlan(deduped, estimated, remaining, complexity, strategy=strategy)

    def register_usage(self, task: Task, consumed_tokens: int) -> None:
        session_id = task.session_id or "default"
        current = self._session_token_usage.get(session_id, 0)
        self._session_token_usage[session_id] = max(0, current + max(0, consumed_tokens))

    def block_model(self, task: Task, model: str) -> None:
        session_id = task.session_id or "default"
        blocked = self._session_blocked_models.setdefault(session_id, set())
        blocked.add(model)


# Legacy compatibility aliases.
GeminiBudgetExhaustedError = AntigravityBudgetExhaustedError
GeminiRoutingPlan = AntigravityRoutingPlan
GeminiRuntimeRouter = AntigravityRuntimeRouter
