from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from .models import Complexity, Priority, Task, TaskType

logger = logging.getLogger(__name__)

BASE_HIGH_RISK_KEYWORDS = ["security", "auth", "rbac", "payment", "secret", "production", "migration", "destructive"]
PERMISSION_CONTEXT_KEYWORDS = ["auth", "authorization", "role", "rbac", "admin", "security", "token", "database", "migration", "tenant"]
LOW_RISK_PERMISSION_EXEMPTIONS = ["permissions-sync-fix", "permission docs cleanup", "permission ui label", "permission comments", "permission formatting"]


@dataclass(slots=True)
class RiskEvaluation:
    detected_keywords: list[str]
    matched_high_risk_rules: list[str]
    matched_low_risk_exemptions: list[str]
    high_risk: bool


@dataclass(slots=True)
class ModelChoice:
    model_name: str
    provider: str
    complexity: Complexity
    requires_secondary_review: bool = False
    detected_keywords: list[str] | None = None
    matched_high_risk_rules: list[str] | None = None
    matched_low_risk_exemptions: list[str] | None = None
    reason: str = "policy_default"


class ModelSelector:
    def __init__(self) -> None:
        self.policy_mode = os.getenv("AI_BRIDGE_POLICY_MODE", "legacy").strip().lower()

    def classify(self, task: Task) -> Complexity:
        if task.complexity:
            return task.complexity
        text = task.input.description.lower()
        risk = evaluate_risk_context(text)
        if task.priority == Priority.CRITICAL or risk.high_risk:
            return Complexity.CRITICAL
        if task.type in {TaskType.PLAN, TaskType.REVIEW} or any(w in text for w in ("architecture", "distributed", "debugging")):
            return Complexity.HIGH
        if risk.matched_low_risk_exemptions and task.type in {TaskType.DOCS, TaskType.FIX} and len(task.input.files) <= 2 and len(text) < 120:
            return Complexity.LOW
        if task.type in {TaskType.CODE, TaskType.TEST, TaskType.FIX, TaskType.DOCS, TaskType.RESEARCH} or len(task.input.files) > 2:
            return Complexity.MEDIUM
        return Complexity.LOW

    def _select_legacy(self, task: Task, complexity: Complexity) -> ModelChoice:
        if complexity == Complexity.CRITICAL:
            return ModelChoice("gpt-senior-secure", "openai", complexity, True, reason="critical_risk_openai_escalation")
        if complexity == Complexity.HIGH:
            if task.type in {TaskType.PLAN, TaskType.REVIEW}:
                return ModelChoice("gpt-coding-large", "openai", complexity, True, reason="high_complexity_openai_escalation")
            return ModelChoice("gemini-2.5-pro", "google", complexity, True, reason="high_reasoning_gemini_pro")
        if complexity == Complexity.LOW:
            return ModelChoice("local-small", "local", complexity, False, reason="low_simple_local_routing")

        if task.type in {TaskType.CODE, TaskType.FIX, TaskType.TEST}:
            return ModelChoice("mistral-small-or-medium", "mistral", complexity, False, reason="medium_code_fix_test_routing")
        if task.type in {TaskType.DOCS, TaskType.RESEARCH, TaskType.REVIEW}:
            return ModelChoice("gemini-cli", "google", complexity, False, reason="medium_docs_research_review_routing")
        return ModelChoice("local-small", "local", complexity, False, reason="policy_default")

    def _select_strict(self, task: Task, complexity: Complexity) -> ModelChoice:
        # strict minimizes OpenAI except explicit critical/high-risk.
        if complexity == Complexity.CRITICAL:
            return ModelChoice("gpt-senior-secure", "openai", complexity, True, reason="critical_openai_only")
        if complexity == Complexity.HIGH:
            if task.type in {TaskType.PLAN, TaskType.REVIEW}:
                return ModelChoice("gemini-2.5-pro", "google", complexity, True, reason="high_plan_review_gemini_pro")
            return ModelChoice("mistral-large-latest", "mistral", complexity, True, reason="high_noncritical_mistral")
        if task.type in {TaskType.CODE, TaskType.FIX, TaskType.TEST}:
            return ModelChoice("mistral-small-or-medium", "mistral", complexity, False, reason="strict_code_mistral")
        return ModelChoice("gemini-2.5-flash-lite", "google", complexity, False, reason="strict_docs_research_gemini")

    def select(self, task: Task) -> ModelChoice:
        complexity = self.classify(task)
        if self.policy_mode == "strict":
            choice = self._select_strict(task, complexity)
        else:
            choice = self._select_legacy(task, complexity)

        logger.info("[MODEL_SELECTOR] complexity=%s task_type=%s preferred_provider=%s assigned_model=%s policy_mode=%s", choice.complexity.value, task.type.value, choice.provider, choice.model_name, self.policy_mode)
        return choice


def evaluate_risk_context(text: str) -> RiskEvaluation:
    normalized = text.lower()
    detected_keywords: list[str] = []
    matched_high_risk_rules: list[str] = []
    matched_low_risk_exemptions: list[str] = []

    for k in BASE_HIGH_RISK_KEYWORDS:
        if k in normalized:
            detected_keywords.append(k)
            matched_high_risk_rules.append(f"base:{k}")

    has_permission = "permission" in normalized or "permissions" in normalized
    if has_permission:
        detected_keywords.append("permission")
        for k in PERMISSION_CONTEXT_KEYWORDS:
            if k in normalized:
                matched_high_risk_rules.append(f"permission+{k}")
        for p in LOW_RISK_PERMISSION_EXEMPTIONS:
            if p in normalized:
                matched_low_risk_exemptions.append(p)

    if matched_low_risk_exemptions and has_permission:
        matched_high_risk_rules = [r for r in matched_high_risk_rules if not r.startswith("permission+")]

    return RiskEvaluation(sorted(set(detected_keywords)), sorted(set(matched_high_risk_rules)), sorted(set(matched_low_risk_exemptions)), bool(matched_high_risk_rules))
