from __future__ import annotations

import os
from dataclasses import dataclass

from .models import Complexity, Task, TaskType
from .openai_model_registry import OpenAIModelRegistry


class OpenAIModelUnavailableError(RuntimeError):
    pass


@dataclass(slots=True)
class OpenAIRoutingPlan:
    models: list[str]
    estimated_tokens: int
    remaining_tokens: int
    complexity: Complexity
    reason: str


class OpenAIRuntimeRouter:
    _session_token_usage: dict[str, int] = {}
    _session_blocked_models: dict[str, set[str]] = {}

    def __init__(self) -> None:
        self.session_budget = self._read_int("OPENAI_SESSION_TOKEN_BUDGET", 120_000)
        self.registry = OpenAIModelRegistry()

    @staticmethod
    def enabled() -> bool:
        return os.getenv("AI_BRIDGE_OPENAI_AUTO_MODEL", "true").strip().lower() in {"1", "true", "yes", "on"}

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
            return 512
        if complexity == Complexity.MEDIUM:
            return 1536
        if complexity == Complexity.HIGH:
            return 4096
        return 8192

    @staticmethod
    def _env_models(key: str) -> list[str]:
        raw = os.getenv(key, "").strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    @staticmethod
    def _fallbacks(complexity: Complexity, task: Task) -> list[str]:
        codex_task = task.type in {TaskType.CODE, TaskType.FIX, TaskType.TEST}
        if complexity == Complexity.LOW:
            return ["gpt-5-nano", "gpt-4.1-nano", "gpt-4o-mini"]
        if complexity == Complexity.MEDIUM:
            return ["gpt-5-mini", "gpt-4.1-mini", "gpt-4o-mini", "gpt-4.1"]
        if complexity == Complexity.HIGH:
            return ["gpt-5.1-codex", "gpt-5-codex", "gpt-5.1", "gpt-5", "gpt-4.1"] if codex_task else ["gpt-5.1", "gpt-5", "gpt-4.1", "gpt-4o"]
        return ["gpt-5.2-codex", "gpt-5.1-codex-max", "gpt-5.2", "gpt-5.2-pro", "gpt-5.1", "gpt-5"]

    def _complexity_ordered_models(self, task: Task, complexity: Complexity, *, force_refresh: bool = False) -> list[str]:
        catalog = self.registry.get_catalog(force_refresh=force_refresh)
        codex_task = task.type in {TaskType.CODE, TaskType.FIX, TaskType.TEST}
        if complexity == Complexity.LOW:
            live = catalog.nano + catalog.mini + catalog.standard
            env_key = "OPENAI_LOW_MODELS"
            reason = "low_cost"
        elif complexity == Complexity.MEDIUM:
            live = catalog.mini + catalog.standard + catalog.nano
            env_key = "OPENAI_MEDIUM_MODELS"
            reason = "balanced_cost"
        elif complexity == Complexity.HIGH:
            live = (catalog.codex + catalog.standard + catalog.pro + catalog.reasoning) if codex_task else (catalog.standard + catalog.pro + catalog.reasoning + catalog.codex)
            env_key = "OPENAI_HIGH_MODELS"
            reason = "high_reasoning"
        else:
            live = (catalog.codex + catalog.pro + catalog.reasoning + catalog.standard) if codex_task else (catalog.pro + catalog.reasoning + catalog.standard + catalog.codex)
            env_key = "OPENAI_CRITICAL_MODELS"
            reason = "critical_quality"

        models = [*self._env_models(env_key), *live, *self._fallbacks(complexity, task), *self._env_models("OPENAI_EXTRA_MODELS")]
        return self._dedupe(models), reason

    @staticmethod
    def _dedupe(models: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for model in models:
            if model in seen:
                continue
            seen.add(model)
            deduped.append(model)
        return deduped

    def build_plan(self, task: Task, prompt: str = "") -> OpenAIRoutingPlan:
        complexity = task.complexity or Complexity.MEDIUM
        estimated = self._estimate_prompt_tokens(prompt or task.input.description) + self._estimate_completion_tokens(complexity)
        session_id = task.session_id or "default"
        used = self._session_token_usage.get(session_id, 0)
        remaining = max(0, self.session_budget - used)

        if remaining <= 0:
            models = ["gpt-5-nano", "gpt-4.1-nano", "gpt-4o-mini"]
            reason = "budget_depleted_lightweight_only"
        else:
            first_call = used <= 0
            models, reason = self._complexity_ordered_models(task, complexity, force_refresh=first_call)
            if estimated > remaining:
                lightweight = ["gpt-5-nano", "gpt-5-mini", "gpt-4.1-nano", "gpt-4.1-mini", "gpt-4o-mini"]
                models = self._dedupe(lightweight + models)
                reason = "budget_guard_lightweight"

        blocked = self._session_blocked_models.get(session_id, set())
        models = [model for model in models if model not in blocked]
        if not models:
            raise OpenAIModelUnavailableError("no OpenAI models available for runtime routing")
        return OpenAIRoutingPlan(models, estimated, remaining, complexity, reason)

    def select_model(self, task: Task, prompt: str = "") -> str:
        return self.build_plan(task, prompt).models[0]

    def register_usage(self, task: Task, consumed_tokens: int) -> None:
        session_id = task.session_id or "default"
        current = self._session_token_usage.get(session_id, 0)
        self._session_token_usage[session_id] = max(0, current + max(0, consumed_tokens))

    def block_model(self, task: Task, model: str) -> None:
        session_id = task.session_id or "default"
        blocked = self._session_blocked_models.setdefault(session_id, set())
        blocked.add(model)
