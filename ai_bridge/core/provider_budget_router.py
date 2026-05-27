from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass

from .model_selector import ModelChoice
from .models import Priority, Task, TaskType


from datetime import UTC, datetime, timedelta

@dataclass(slots=True)
class ProviderState:
    exhausted_until: datetime | None = None
    failures: int = 0

    @property
    def exhausted(self) -> bool:
        if self.exhausted_until is None:
            return False
        return datetime.now(UTC) < self.exhausted_until


class ProviderBudgetRouter:
    """Global provider fallback router (separate from Gemini intra-model token router)."""

    def __init__(self) -> None:
        self._session_provider_state: dict[str, dict[str, ProviderState]] = defaultdict(dict)
        self.force_gemini = os.getenv("AI_BRIDGE_FORCE_GEMINI", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.recovery_timeout_min = int(os.getenv("AI_BRIDGE_RECOVERY_TIMEOUT_MIN", "5"))

    @staticmethod
    def _session_id(task: Task) -> str:
        return task.session_id or "default"

    @staticmethod
    def _normalize_provider(provider: str) -> str:
        p = provider.strip().lower()
        if p in {"google", "gemini", "gemini-cli"}:
            return "google"
        return p

    def _state(self, task: Task, provider: str) -> ProviderState:
        sid = self._session_id(task)
        key = self._normalize_provider(provider)
        state = self._session_provider_state[sid].get(key)
        if state is None:
            state = ProviderState()
            self._session_provider_state[sid][key] = state
        return state

    def mark_failure(self, task: Task, provider: str, error_type: str) -> None:
        state = self._state(task, provider)
        state.failures += 1
        if error_type in {"quota_exhaustion", "auth_fail"}:
            state.exhausted_until = datetime.now(UTC) + timedelta(minutes=self.recovery_timeout_min)

    def register_success(self, task: Task, provider: str) -> None:
        state = self._state(task, provider)
        state.failures = 0
        state.exhausted_until = None

    def preferred_providers(self, task: Task, choice: ModelChoice) -> list[str]:
        preferred = self._normalize_provider(choice.provider)

        # Keep high-risk planning/review on OpenAI first.
        if task.priority in {Priority.HIGH, Priority.CRITICAL} and task.type in {TaskType.PLAN, TaskType.REVIEW}:
            base = ["openai", "google", "mistral", "local"]
        elif self.force_gemini and task.type in {TaskType.CODE, TaskType.TEST, TaskType.DOCS, TaskType.RESEARCH, TaskType.REVIEW, TaskType.FIX}:
            base = ["google", "mistral", "openai", "local"]
        elif task.type in {TaskType.CODE, TaskType.TEST, TaskType.FIX}:
            base = ["google", preferred, "mistral", "openai", "local"]
        elif task.type in {TaskType.DOCS, TaskType.RESEARCH, TaskType.REVIEW}:
            base = [preferred, "google", "mistral", "openai", "local"]
        else:
            base = [preferred, "openai", "google", "mistral", "local"]

        seen: set[str] = set()
        ranked: list[str] = []
        for p in base:
            norm = self._normalize_provider(p)
            if norm in seen:
                continue
            seen.add(norm)
            state = self._state(task, norm)
            if state.exhausted:
                continue
            ranked.append(norm)
        return ranked or ["openai", "google", "mistral", "local"]
