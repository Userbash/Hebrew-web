from __future__ import annotations

import os
from dataclasses import dataclass

from .models import Complexity, Task


class GeminiBudgetExhaustedError(RuntimeError):
    pass


@dataclass(slots=True)
class GeminiRoutingPlan:
    models: list[str]
    estimated_tokens: int
    remaining_tokens: int
    complexity: Complexity


class GeminiRuntimeRouter:
    _session_token_usage: dict[str, int] = {}

    def __init__(self) -> None:
        self.session_budget = self._read_int("GEMINI_SESSION_TOKEN_BUDGET", 200_000)

    @staticmethod
    def _read_int(key: str, default: int) -> int:
        raw = os.getenv(key, str(default)).strip()
        try:
            return int(raw)
        except ValueError:
            return default

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

    @staticmethod
    def _complexity_ordered_models(complexity: Complexity) -> list[str]:
        if complexity == Complexity.LOW:
            return ["gemini-2.5-flash-lite", "gemini-3-flash-preview", "gemini-1.5-flash"]
        if complexity == Complexity.MEDIUM:
            return ["gemini-3-flash-preview", "gemini-2.0-flash-exp", "gemini-1.5-pro"]
        if complexity == Complexity.HIGH:
            return ["gemini-2.5-pro", "gemini-3-flash-preview", "gemini-1.5-pro"]
        return ["gemini-3-flash-preview", "gemini-1.5-pro", "gemini-2.0-pro-exp"]

    @staticmethod
    def _parse_extra_fallbacks() -> list[str]:
        raw = os.getenv("GEMINI_CLI_EXTRA_MODELS", "").strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    def build_plan(self, task: Task, prompt: str) -> GeminiRoutingPlan:
        complexity = task.complexity or Complexity.MEDIUM
        estimated = self._estimate_prompt_tokens(prompt) + self._estimate_completion_tokens(complexity)
        session_id = task.session_id or "default"
        used = self._session_token_usage.get(session_id, 0)
        remaining = max(0, self.session_budget - used)

        if remaining <= 0 or estimated > remaining * 2:
            # If budget is almost depleted, use only lightweight model.
            models = ["gemini-2.5-flash-lite"]
        else:
            models = self._complexity_ordered_models(complexity)

        extra = self._parse_extra_fallbacks()
        seen: set[str] = set()
        deduped: list[str] = []
        for model in [*models, *extra]:
            if model in seen:
                continue
            seen.add(model)
            deduped.append(model)

        if not deduped:
            raise GeminiBudgetExhaustedError("no models available for runtime routing")

        return GeminiRoutingPlan(deduped, estimated, remaining, complexity)

    def register_usage(self, task: Task, consumed_tokens: int) -> None:
        session_id = task.session_id or "default"
        current = self._session_token_usage.get(session_id, 0)
        self._session_token_usage[session_id] = max(0, current + max(0, consumed_tokens))
