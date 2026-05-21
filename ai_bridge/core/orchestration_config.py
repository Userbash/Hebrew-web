from __future__ import annotations

import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Any

class ExecutionMode(Enum):
    MANUAL = "manual"
    ASSISTED = "assisted"
    AUTO_SAFE = "auto_safe"
    FULL_AUTO = "full_auto"
    CI = "ci"

class RiskLevel(Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    HIGH = "high"
    DESTRUCTIVE = "destructive"
    EXTERNAL_SIDE_EFFECT = "external_side_effect"
    PRODUCTION_CRITICAL = "production_critical"

class RiskClassifier:
    @staticmethod
    def classify(task: Any) -> RiskLevel:
        markers = set(_get_value(task, "markers", []) or [])
        action = str(_get_value(task, "action", "") or _get_value(task, "type", "")).lower()

        if "production_critical" in markers or action in {"production_deploy"}:
            return RiskLevel.PRODUCTION_CRITICAL
        if "destructive" in markers or action in {"database_delete", "force_push"}:
            return RiskLevel.DESTRUCTIVE
        if "external" in markers or action in {"external_api_calls"}:
            return RiskLevel.EXTERNAL_SIDE_EFFECT
        if action in {"security", "secret_rotation"}:
            return RiskLevel.HIGH
        if action in {"code_generation", "test", "refactor"}:
            return RiskLevel.SAFE
        return RiskLevel.MODERATE

class PolicyEngine:
    @staticmethod
    def evaluate(task: Any) -> bool:
        risk = RiskClassifier.classify(task)
        if risk in {RiskLevel.DESTRUCTIVE, RiskLevel.PRODUCTION_CRITICAL}:
            return False
        return True

SAFE_STANDARD_TASK_TYPES = {
    "code_generation",
    "code",
    "tests",
    "test",
    "review",
    "docs",
    "documentation",
    "refactor",
    "local_scripts",
    "healthcheck",
    "metrics",
    "task_routing",
}
...

DESTRUCTIVE_MARKERS = {
    "production_deploy",
    "database_delete",
    "delete_production_data",
    "secret_change",
    "rotate_keys",
    "payment_action",
    "modify_billing",
    "external_email",
    "public_api_mutation",
    "force_push",
}


@dataclass(slots=True)
class ConfirmationPolicy:
    ask_for_low_risk_tasks: bool = False
    ask_for_medium_risk_tasks: bool = False
    ask_for_high_risk_tasks: bool = True
    ask_for_destructive_actions: bool = True
    ask_for_external_api_calls: bool = True


@dataclass(slots=True)
class SafetyGuards:
    allow_auto_code_changes: bool = True
    allow_auto_tests: bool = True
    allow_auto_docs: bool = True
    allow_auto_refactor: bool = True
    require_confirmation_for: list[str] = field(default_factory=lambda: sorted(DESTRUCTIVE_MARKERS))


@dataclass(slots=True)
class OrchestrationConfig:
    enabled_by_default: bool = True
    ask_confirmation: bool = False
    default_mode: str = "ai_bridge"
    auto_route_tasks: bool = True
    auto_start_agents: bool = True
    auto_retry: bool = True
    auto_review: bool = True
    auto_test: bool = True
    auto_approve_safe_tasks: bool = True
    require_confirmation_for_destructive: bool = True
    default_engine: str = "ai_bridge"
    non_interactive: bool = True
    confirmation_policy: ConfirmationPolicy = field(default_factory=ConfirmationPolicy)
    safety_guards: SafetyGuards = field(default_factory=SafetyGuards)

    @classmethod
    def from_env(cls) -> OrchestrationConfig:
        enabled = _env_bool("AI_BRIDGE_ENABLED", True) and _env_bool("AI_BRIDGE_DEFAULT", True)
        auto_approve = _env_bool("AI_BRIDGE_AUTO_APPROVE", True)
        non_interactive = _env_bool("AI_BRIDGE_NON_INTERACTIVE", True)
        safe_only = os.getenv("AI_BRIDGE_CONFIRMATION_POLICY", "safe-only").lower() == "safe-only"
        return cls(
            enabled_by_default=enabled,
            ask_confirmation=not auto_approve,
            auto_approve_safe_tasks=auto_approve,
            non_interactive=non_interactive,
            confirmation_policy=ConfirmationPolicy(
                ask_for_low_risk_tasks=False if safe_only else not auto_approve,
                ask_for_medium_risk_tasks=False if safe_only else not auto_approve,
                ask_for_high_risk_tasks=True,
                ask_for_destructive_actions=True,
                ask_for_external_api_calls=True,
            ),
        )

    def apply_cli_flags(self, *, yes: bool = False, auto: bool = False, use_bridge: bool = False, non_interactive: bool = False) -> None:
        if yes or auto:
            self.ask_confirmation = False
            self.auto_approve_safe_tasks = True
        if use_bridge:
            self.enabled_by_default = True
            self.default_mode = "ai_bridge"
            self.default_engine = "ai_bridge"
        if non_interactive:
            self.non_interactive = True

    def should_ask_confirmation(self, task: Any) -> bool:
        if not self.enabled_by_default:
            return True
        if _get_bool(task, "manual_only"):
            return True
        if _get_bool(task, "is_destructive") and self.confirmation_policy.ask_for_destructive_actions:
            return True
        if _get_bool(task, "requires_external_side_effect") and self.confirmation_policy.ask_for_external_api_calls:
            return True

        action = str(_get_value(task, "action", "") or _get_value(task, "type", "")).lower()
        markers = set(_get_value(task, "markers", []) or [])
        marker_hit = action in DESTRUCTIVE_MARKERS or bool(markers.intersection(DESTRUCTIVE_MARKERS))
        if marker_hit and self.require_confirmation_for_destructive:
            return True

        risk_level = str(_get_value(task, "risk_level", "low") or "low").lower()
        if risk_level in {"critical", "unsafe"}:
            return True
        if risk_level == "high":
            return self.confirmation_policy.ask_for_high_risk_tasks
        if risk_level == "medium":
            return self.confirmation_policy.ask_for_medium_risk_tasks
        if risk_level == "low":
            return self.confirmation_policy.ask_for_low_risk_tasks

        if action in SAFE_STANDARD_TASK_TYPES and self.auto_approve_safe_tasks:
            return False
        return self.ask_confirmation

    def as_dict(self) -> dict[str, Any]:
        return {
            "enabled_by_default": self.enabled_by_default,
            "ask_confirmation": self.ask_confirmation,
            "default_mode": self.default_mode,
            "auto_route_tasks": self.auto_route_tasks,
            "auto_start_agents": self.auto_start_agents,
            "auto_retry": self.auto_retry,
            "auto_review": self.auto_review,
            "auto_test": self.auto_test,
            "auto_approve_safe_tasks": self.auto_approve_safe_tasks,
            "require_confirmation_for_destructive": self.require_confirmation_for_destructive,
            "default_engine": self.default_engine,
            "non_interactive": self.non_interactive,
        }


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_bool(task: Any, name: str) -> bool:
    return bool(_get_value(task, name, False))


def _get_value(task: Any, name: str, default: Any = None) -> Any:
    if isinstance(task, dict):
        return task.get(name, default)
    return getattr(task, name, default)
