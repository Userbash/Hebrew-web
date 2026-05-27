from __future__ import annotations

import logging
from dataclasses import dataclass

from .models import Complexity, Priority, RoutingTrace, ScoreBreakdown, Task, TaskType

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

    def _score_model(self, model_info: dict, task: Task) -> tuple[ScoreBreakdown, list[RoutingTrace]]:
        # Mocked scoring based on task/context
        # In production, pull real metrics from registry
        traces = []
        
        # Capability (e.g. Codex/Codestral is high for CODE)
        is_coding = "coding" in model_info['model_name'] or "codestral" in model_info['model_name']
        cap = 0.95 if is_coding and task.type == TaskType.CODE else 0.7
        
        # Reliability/Safety (e.g. GPT-4/Pro models are safe)
        is_pro = "pro" in model_info['model_name'] or "gpt-4" in model_info['model_name'] or "large" in model_info['model_name']
        safety = 0.95 if is_pro else 0.8
        
        # Context (Gemini is high for research/long context)
        is_gemini = "gemini" in model_info['model_name']
        context = 0.95 if is_gemini and task.type == TaskType.RESEARCH else 0.6
        
        # Latency (Flash models are fast)
        is_flash = "flash" in model_info['model_name'] or "small" in model_info['model_name']
        latency = 0.9 if is_flash else 0.7

        breakdown = ScoreBreakdown(cap, 0.8, latency, 0.5, context, safety)
        
        # Apply penalties from CB
        penalty = CircuitBreaker.get_penalty(model_info['provider'], 0.05, 500)
        if penalty < 0:
            traces.append(RoutingTrace("circuit_breaker_penalty", model_info['provider'], penalty, "High error rate or latency"))
        
        traces.append(RoutingTrace("base_score", "all", 0.0, "Initial model assessment"))
        
        return breakdown, traces

    def select(self, task: Task) -> ModelChoice:
        candidates = [
            {"model_name": "local-small", "provider": "local"},
            {"model_name": "mistral-large-latest", "provider": "mistral"},
            {"model_name": "codestral-latest", "provider": "mistral"},
            {"model_name": "gemini-3-flash-preview", "provider": "google"},
            {"model_name": "gemini-1.5-pro", "provider": "google"},
            {"model_name": "gpt-coding-large", "provider": "openai"},
            {"model_name": "gpt-4o", "provider": "openai"}
        ]
        
        results = {}
        for m in candidates:
            breakdown, traces = self._score_model(m, task)
            results[m['model_name']] = {
                "breakdown": breakdown,
                "score": breakdown.total(WEIGHTS),
                "trace": traces
            }
            
        best_name = max(results, key=lambda k: results[k]["score"])
        best_data = results[best_name]
        
        confidence = min(0.95, 0.5 + (best_data["score"] / 2))
        
        choice = ModelChoice(
            model_name=best_name,
            provider=next(c['provider'] for c in candidates if c['model_name'] == best_name),
            complexity=task.complexity or Complexity.MEDIUM,
            requires_secondary_review=(confidence < 0.6 or task.priority == Priority.CRITICAL),
            reason=f"weighted_scoring_routing_confidence_{confidence:.2f}"
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
