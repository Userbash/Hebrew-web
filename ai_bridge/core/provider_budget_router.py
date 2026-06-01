from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .model_selector import ModelChoice
from .models import Priority, Task, TaskType, Complexity


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
        self.policy_mode = os.getenv("AI_BRIDGE_POLICY_MODE", "legacy").strip().lower()

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

        is_critical = task.priority in {Priority.CRITICAL} or choice.complexity == Complexity.CRITICAL
        is_high_risk = task.priority in {Priority.HIGH, Priority.CRITICAL} or choice.complexity in {Complexity.HIGH, Complexity.CRITICAL}

        if is_critical:
            # Security-critical first on openai, then resilient fallbacks.
            base = ["openai", "google", "mistral", "local"]
        elif self.policy_mode == "strict":
            # Strict cost-optimization: defer openai to the end for non-critical.
            if task.type in {TaskType.CODE, TaskType.TEST, TaskType.FIX}:
                base = [preferred, "mistral", "google", "local", "openai"]
            else:
                base = [preferred, "google", "mistral", "local", "openai"]
        elif self.force_gemini and task.type in {TaskType.CODE, TaskType.TEST, TaskType.DOCS, TaskType.RESEARCH, TaskType.REVIEW, TaskType.FIX}:
            base = ["google", "mistral", "local", "openai"]
        elif task.type in {TaskType.CODE, TaskType.TEST, TaskType.FIX}:
            base = [preferred, "mistral", "google", "local", "openai"]
        elif task.type in {TaskType.DOCS, TaskType.RESEARCH, TaskType.REVIEW}:
            base = [preferred, "google", "mistral", "local", "openai"]
        elif is_high_risk:
            base = ["google", preferred, "mistral", "local", "openai"]
        else:
            base = [preferred, "google", "mistral", "local", "openai"]

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
        return ranked or ["google", "mistral", "local", "openai"]
