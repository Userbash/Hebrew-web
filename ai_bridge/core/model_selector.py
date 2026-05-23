from __future__ import annotations

import logging
from dataclasses import dataclass

from .models import Complexity, Priority, Task, TaskType

logger = logging.getLogger(__name__)

BASE_HIGH_RISK_KEYWORDS = [
    "security",
    "auth",
    "rbac",
    "payment",
    "secret",
    "production",
    "migration",
    "destructive",
]

PERMISSION_CONTEXT_KEYWORDS = [
    "auth",
    "authentication",
    "authorization",
    "role",
    "roles",
    "rbac",
    "admin",
    "superuser",
    "root",
    "sudo",
    "production",
    "prod",
    "security",
    "exploit",
    "vulnerability",
    "privilege",
    "privilege escalation",
    "access control",
    "token",
    "jwt",
    "session",
    "oauth",
    "api key",
    "secret",
    "database",
    "migration",
    "tenant",
    "multi-tenant",
    "billing",
    "payment",
    "pii",
    "user data",
    "personal data",
    "compliance",
    "audit log",
    "policy",
    "acl",
]

LOW_RISK_PERMISSION_EXEMPTIONS = [
    "permissions-sync-fix",
    "permission docs cleanup",
    "permission label rename",
    "permission ui text",
    "permission frontend display",
    "permission type cleanup",
    "permission test fixture",
    "permission mock update",
    "permission docs",
    "permission comments",
    "permission formatting",
]


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
    def classify(self, task: Task) -> Complexity:
        text = task.input.description.lower()
        risk = evaluate_risk_context(text)
        if task.priority == Priority.CRITICAL or risk.high_risk:
            return Complexity.CRITICAL
        if task.type in {TaskType.PLAN, TaskType.REVIEW} or any(word in text for word in ("architecture", "distributed", "debugging")):
            return Complexity.HIGH

        # Keep low-risk permission cleanup/docs work on low complexity when scope is small.
        if risk.matched_low_risk_exemptions and task.type in {TaskType.DOCS, TaskType.FIX} and len(task.input.files) <= 2 and len(text) < 120 and "permissions-sync-fix" not in text:
            return Complexity.LOW

        if task.type in {TaskType.CODE, TaskType.TEST, TaskType.FIX, TaskType.DOCS, TaskType.RESEARCH} or len(task.input.files) > 2:
            return Complexity.MEDIUM
        return Complexity.LOW

    def select(self, task: Task) -> ModelChoice:
        text = task.input.description.lower()
        risk = evaluate_risk_context(text)
        complexity = Complexity.CRITICAL if risk.high_risk else (task.complexity or self.classify(task))

        if complexity == Complexity.LOW:
            choice = ModelChoice(
                "local-small",
                "local",
                complexity,
                detected_keywords=risk.detected_keywords,
                matched_high_risk_rules=risk.matched_high_risk_rules,
                matched_low_risk_exemptions=risk.matched_low_risk_exemptions,
                reason="low_simple_local_routing",
            )
            self._log_choice(task, choice)
            return choice

        if complexity == Complexity.MEDIUM:
            if task.type in {TaskType.CODE, TaskType.FIX, TaskType.TEST}:
                choice = ModelChoice(
                    "mistral-small-or-medium",
                    "mistral",
                    complexity,
                    detected_keywords=risk.detected_keywords,
                    matched_high_risk_rules=risk.matched_high_risk_rules,
                    matched_low_risk_exemptions=risk.matched_low_risk_exemptions,
                    reason="medium_code_fix_test_routing",
                )
            elif task.type in {TaskType.DOCS, TaskType.RESEARCH, TaskType.REVIEW}:
                choice = ModelChoice(
                    "gemini-cli",
                    "google",
                    complexity,
                    detected_keywords=risk.detected_keywords,
                    matched_high_risk_rules=risk.matched_high_risk_rules,
                    matched_low_risk_exemptions=risk.matched_low_risk_exemptions,
                    reason="medium_docs_research_review_routing",
                )
            else:
                choice = ModelChoice(
                    "mistral-small-or-medium",
                    "mistral",
                    complexity,
                    detected_keywords=risk.detected_keywords,
                    matched_high_risk_rules=risk.matched_high_risk_rules,
                    matched_low_risk_exemptions=risk.matched_low_risk_exemptions,
                    reason="medium_code_fix_test_routing",
                )
            self._log_choice(task, choice)
            return choice

        if complexity == Complexity.HIGH:
            choice = ModelChoice(
                "gpt-coding-large",
                "openai",
                complexity,
                requires_secondary_review=True,
                detected_keywords=risk.detected_keywords,
                matched_high_risk_rules=risk.matched_high_risk_rules,
                matched_low_risk_exemptions=risk.matched_low_risk_exemptions,
                reason="high_complexity_openai_escalation",
            )
            self._log_choice(task, choice)
            return choice

        choice = ModelChoice(
            "gpt-senior-secure",
            "openai",
            complexity,
            requires_secondary_review=True,
            detected_keywords=risk.detected_keywords,
            matched_high_risk_rules=risk.matched_high_risk_rules,
            matched_low_risk_exemptions=risk.matched_low_risk_exemptions,
            reason="critical_risk_openai_escalation",
        )
        self._log_choice(task, choice)
        return choice

    @staticmethod
    def _log_choice(task: Task, choice: ModelChoice) -> None:
        logger.info(
            "[MODEL_SELECTOR] "
            f"complexity={choice.complexity.value} "
            f"task_type={task.type.value} "
            f"preferred_provider={choice.provider} "
            f"assigned_model={choice.model_name}"
        )


def evaluate_risk_context(text: str) -> RiskEvaluation:
    normalized = text.lower()
    detected_keywords: list[str] = []
    matched_high_risk_rules: list[str] = []
    matched_low_risk_exemptions: list[str] = []

    for keyword in BASE_HIGH_RISK_KEYWORDS:
        if keyword in normalized:
            detected_keywords.append(keyword)
            matched_high_risk_rules.append(f"base:{keyword}")

    has_permission_word = "permission" in normalized or "permissions" in normalized
    permission_context_hits: list[str] = []

    if has_permission_word:
        detected_keywords.append("permission")
        for context_keyword in PERMISSION_CONTEXT_KEYWORDS:
            if context_keyword in normalized:
                permission_context_hits.append(context_keyword)
                matched_high_risk_rules.append(f"permission+{context_keyword}")

        for phrase in LOW_RISK_PERMISSION_EXEMPTIONS:
            if phrase in normalized:
                matched_low_risk_exemptions.append(phrase)

        has_exemption = len(matched_low_risk_exemptions) > 0
        if permission_context_hits and not has_exemption:
            for hit in permission_context_hits:
                if hit not in detected_keywords:
                    detected_keywords.append(hit)

    high_risk = len(matched_high_risk_rules) > 0

    # Exemptions only relax permission-triggered escalation, not base high-risk terms.
    if matched_low_risk_exemptions and has_permission_word:
        non_permission_rules = [rule for rule in matched_high_risk_rules if not rule.startswith("permission+")]
        matched_high_risk_rules = non_permission_rules
        high_risk = len(matched_high_risk_rules) > 0

    return RiskEvaluation(
        detected_keywords=sorted(set(detected_keywords)),
        matched_high_risk_rules=sorted(set(matched_high_risk_rules)),
        matched_low_risk_exemptions=sorted(set(matched_low_risk_exemptions)),
        high_risk=high_risk,
    )
