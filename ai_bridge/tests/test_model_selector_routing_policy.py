from __future__ import annotations

from dataclasses import dataclass

import pytest

from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.load_balancer import LoadBalancer
from ai_bridge.core.model_selector import ModelSelector
from ai_bridge.core.models import AgentStatus, Complexity, Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.task_router import TaskRouter


@dataclass(frozen=True, slots=True)
class RoutingCase:
    name: str
    task_type: TaskType
    description: str
    forced_complexity: Complexity | None
    mistral_offline: bool
    expected_complexity: Complexity
    expected_orchestrator: str
    expected_provider: str
    expected_model: str
    expected_fallback: bool
    expected_secondary_review: bool
    expected_reason: str


def _task(task_type: TaskType, description: str, forced_complexity: Complexity | None) -> Task:
    task = Task(task_type, TaskInput(description), TaskContext("p", ".", "main"))
    task.complexity = forced_complexity
    return task


def _build_registry(*, mistral_offline: bool = False) -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(
        "local-orchestrator",
        "custom",
        "local://small",
        ["docs", "fix"],
        model_name="local-small",
        provider="local",
    )
    mistral = registry.register(
        "mistral-orchestrator",
        "custom",
        "local://mistral",
        ["code", "fix", "test"],
        model_name="mistral-small-or-medium",
        provider="mistral",
    )
    registry.register(
        "gemini-cli-orchestrator",
        "custom",
        "local://gemini-cli",
        ["docs", "research", "review"],
        model_name="gemini-cli",
        provider="google",
    )
    registry.register(
        "openai-orchestrator",
        "codex",
        "local://openai-large",
        ["plan"],
        model_name="gpt-coding-large",
        provider="openai",
    )
    registry.register(
        "openai-secure-orchestrator",
        "codex",
        "local://openai-secure",
        ["code", "fix", "test", "docs", "research", "review"],
        model_name="gpt-senior-secure",
        provider="openai",
    )
    registry.register(
        "openai-fallback-orchestrator",
        "codex",
        "local://openai-standard",
        ["code", "fix", "test"],
        model_name="gpt-coding-standard",
        provider="openai",
    )

    if mistral_offline:
        mistral.status = AgentStatus.OFFLINE

    return registry


def _reason(choice_provider: str, choice_complexity: Complexity, fallback_used: bool) -> str:
    if fallback_used:
        return "fallback_non_openai_unavailable"
    if choice_complexity == Complexity.CRITICAL:
        return "critical_risk_openai_escalation"
    if choice_complexity == Complexity.HIGH:
        return "high_complexity_openai_escalation"
    if choice_provider == "local":
        return "low_simple_local_routing"
    if choice_provider == "mistral":
        return "medium_code_fix_test_routing"
    if choice_provider == "google":
        return "medium_docs_research_review_routing"
    return "policy_default"


def _execute_case(case: RoutingCase) -> dict[str, object]:
    task = _task(case.task_type, case.description, case.forced_complexity)
    selector = ModelSelector()
    choice = selector.select(task)

    router = TaskRouter(_build_registry(mistral_offline=case.mistral_offline), LoadBalancer())
    acceptance = router.route(task)
    assert acceptance.status.value == "accepted"

    agent = router.registry.get(acceptance.assigned_agent)
    assert agent is not None

    fallback_used = choice.provider != "openai" and agent.provider == "openai"
    selected_model = "gpt-coding-standard" if fallback_used else choice.model_name

    return {
        "task": case.name,
        "task_type": task.type.value,
        "complexity": choice.complexity,
        "selected_orchestrator": agent.id,
        "selected_provider": agent.provider,
        "selected_model": selected_model,
        "fallback_used": fallback_used,
        "requires_secondary_review": choice.requires_secondary_review,
        "reason": _reason(choice.provider, choice.complexity, fallback_used),
    }


CASES = [
    RoutingCase(
        name="simple docs cleanup",
        task_type=TaskType.DOCS,
        description="cleanup docs formatting and spacing",
        forced_complexity=Complexity.LOW,
        mistral_offline=False,
        expected_complexity=Complexity.LOW,
        expected_orchestrator="local-orchestrator",
        expected_provider="local",
        expected_model="local-small",
        expected_fallback=False,
        expected_secondary_review=False,
        expected_reason="low_simple_local_routing",
    ),
    RoutingCase(
        name="simple typo fix",
        task_type=TaskType.FIX,
        description="fix one typo",
        forced_complexity=Complexity.LOW,
        mistral_offline=False,
        expected_complexity=Complexity.LOW,
        expected_orchestrator="local-orchestrator",
        expected_provider="local",
        expected_model="local-small",
        expected_fallback=False,
        expected_secondary_review=False,
        expected_reason="low_simple_local_routing",
    ),
    RoutingCase(
        name="medium code refactor",
        task_type=TaskType.CODE,
        description="refactor service module",
        forced_complexity=Complexity.MEDIUM,
        mistral_offline=False,
        expected_complexity=Complexity.MEDIUM,
        expected_orchestrator="mistral-orchestrator",
        expected_provider="mistral",
        expected_model="mistral-small-or-medium",
        expected_fallback=False,
        expected_secondary_review=False,
        expected_reason="medium_code_fix_test_routing",
    ),
    RoutingCase(
        name="medium unit test generation",
        task_type=TaskType.TEST,
        description="generate unit tests for parser",
        forced_complexity=Complexity.MEDIUM,
        mistral_offline=False,
        expected_complexity=Complexity.MEDIUM,
        expected_orchestrator="mistral-orchestrator",
        expected_provider="mistral",
        expected_model="mistral-small-or-medium",
        expected_fallback=False,
        expected_secondary_review=False,
        expected_reason="medium_code_fix_test_routing",
    ),
    RoutingCase(
        name="medium documentation update",
        task_type=TaskType.DOCS,
        description="update API docs",
        forced_complexity=Complexity.MEDIUM,
        mistral_offline=False,
        expected_complexity=Complexity.MEDIUM,
        expected_orchestrator="gemini-cli-orchestrator",
        expected_provider="google",
        expected_model="gemini-cli",
        expected_fallback=False,
        expected_secondary_review=False,
        expected_reason="medium_docs_research_review_routing",
    ),
    RoutingCase(
        name="medium research task",
        task_type=TaskType.RESEARCH,
        description="research options for caching",
        forced_complexity=Complexity.MEDIUM,
        mistral_offline=False,
        expected_complexity=Complexity.MEDIUM,
        expected_orchestrator="gemini-cli-orchestrator",
        expected_provider="google",
        expected_model="gemini-cli",
        expected_fallback=False,
        expected_secondary_review=False,
        expected_reason="medium_docs_research_review_routing",
    ),
    RoutingCase(
        name="high architecture redesign",
        task_type=TaskType.PLAN,
        description="high level architecture redesign for distributed services",
        forced_complexity=Complexity.HIGH,
        mistral_offline=False,
        expected_complexity=Complexity.HIGH,
        expected_orchestrator="openai-orchestrator",
        expected_provider="openai",
        expected_model="gpt-coding-large",
        expected_fallback=False,
        expected_secondary_review=True,
        expected_reason="high_complexity_openai_escalation",
    ),
    RoutingCase(
        name="critical auth/security fix",
        task_type=TaskType.FIX,
        description="critical auth security fix with permission checks",
        forced_complexity=None,
        mistral_offline=False,
        expected_complexity=Complexity.CRITICAL,
        expected_orchestrator="openai-secure-orchestrator",
        expected_provider="openai",
        expected_model="gpt-senior-secure",
        expected_fallback=False,
        expected_secondary_review=True,
        expected_reason="critical_risk_openai_escalation",
    ),
    RoutingCase(
        name="production migration",
        task_type=TaskType.FIX,
        description="production migration for database",
        forced_complexity=None,
        mistral_offline=False,
        expected_complexity=Complexity.CRITICAL,
        expected_orchestrator="openai-secure-orchestrator",
        expected_provider="openai",
        expected_model="gpt-senior-secure",
        expected_fallback=False,
        expected_secondary_review=True,
        expected_reason="critical_risk_openai_escalation",
    ),
    RoutingCase(
        name="destructive database operation",
        task_type=TaskType.FIX,
        description="destructive database operation with data rewrite",
        forced_complexity=None,
        mistral_offline=False,
        expected_complexity=Complexity.CRITICAL,
        expected_orchestrator="openai-secure-orchestrator",
        expected_provider="openai",
        expected_model="gpt-senior-secure",
        expected_fallback=False,
        expected_secondary_review=True,
        expected_reason="critical_risk_openai_escalation",
    ),
    RoutingCase(
        name="mistral unavailable fallback",
        task_type=TaskType.CODE,
        description="implement parser",
        forced_complexity=Complexity.MEDIUM,
        mistral_offline=True,
        expected_complexity=Complexity.MEDIUM,
        expected_orchestrator="openai-fallback-orchestrator",
        expected_provider="openai",
        expected_model="gpt-coding-standard",
        expected_fallback=True,
        expected_secondary_review=False,
        expected_reason="fallback_non_openai_unavailable",
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[case.name for case in CASES])
def test_routing_policy_matrix(case: RoutingCase):
    result = _execute_case(case)

    assert result["task_type"] == case.task_type.value
    assert result["complexity"] == case.expected_complexity
    assert result["selected_orchestrator"] == case.expected_orchestrator
    assert result["selected_provider"] == case.expected_provider
    assert result["selected_model"] == case.expected_model
    assert result["fallback_used"] is case.expected_fallback
    assert result["requires_secondary_review"] is case.expected_secondary_review
    assert result["reason"] == case.expected_reason


def test_permission_sync_fix_not_critical():
    choice = ModelSelector().select(_task(TaskType.FIX, "permissions-sync-fix", None))
    router = TaskRouter(_build_registry(mistral_offline=False), LoadBalancer())
    accepted = router.route(_task(TaskType.FIX, "permissions-sync-fix", None))
    agent = router.registry.get(accepted.assigned_agent)

    assert choice.complexity != Complexity.CRITICAL
    assert not choice.requires_secondary_review
    assert agent is not None
    assert agent.id != "openai-secure-orchestrator"


def test_permission_ui_label_low_medium_local_route():
    task = _task(TaskType.DOCS, "fix permission UI label", None)
    choice = ModelSelector().select(task)
    router = TaskRouter(_build_registry(mistral_offline=False), LoadBalancer())
    accepted = router.route(task)
    agent = router.registry.get(accepted.assigned_agent)

    assert choice.complexity in {Complexity.LOW, Complexity.MEDIUM}
    assert agent is not None
    assert agent.provider == "local"


def test_permission_escalation_admin_auth_is_critical_secure():
    task = _task(TaskType.FIX, "fix permission escalation in admin role auth", None)
    choice = ModelSelector().select(task)
    router = TaskRouter(_build_registry(mistral_offline=False), LoadBalancer())
    accepted = router.route(task)
    agent = router.registry.get(accepted.assigned_agent)

    assert choice.complexity == Complexity.CRITICAL
    assert choice.requires_secondary_review
    assert agent is not None
    assert agent.id == "openai-secure-orchestrator"


def test_rbac_permission_production_tenant_data_is_critical_secure():
    task = _task(TaskType.FIX, "update RBAC permission checks for production tenant data", None)
    choice = ModelSelector().select(task)
    router = TaskRouter(_build_registry(mistral_offline=False), LoadBalancer())
    accepted = router.route(task)
    agent = router.registry.get(accepted.assigned_agent)

    assert choice.complexity == Complexity.CRITICAL
    assert choice.requires_secondary_review
    assert agent is not None
    assert agent.id == "openai-secure-orchestrator"


def test_permission_docs_cleanup_low_local_route():
    task = _task(TaskType.DOCS, "permission docs cleanup", None)
    choice = ModelSelector().select(task)
    router = TaskRouter(_build_registry(mistral_offline=False), LoadBalancer())
    accepted = router.route(task)
    agent = router.registry.get(accepted.assigned_agent)

    assert choice.complexity == Complexity.LOW
    assert not choice.requires_secondary_review
    assert agent is not None
    assert agent.provider == "local"
