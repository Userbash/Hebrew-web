from __future__ import annotations

from ai_bridge.agents.codex_agent import CodexAgent
from ai_bridge.agents.gemini_cli_agent import GeminiCLIAgent
from ai_bridge.agents.planner_agent import PlannerAgent
from ai_bridge.agents.reviewer_agent import ReviewerAgent
from ai_bridge.agents.tester_agent import TesterAgent
from ai_bridge.core.models import Priority, Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.core.provider_budget_router import ProviderBudgetRouter
from ai_bridge.core.security import SecurityManager, SecurityPolicy
from ai_bridge.core.task_decomposer import TaskDecomposer


def test_decomposer_sets_code_test_normal_and_review_high():
    root = Task(
        TaskType.PLAN,
        TaskInput("Improve orchestrator and monitoring"),
        TaskContext("demo", ".", "main"),
        priority=Priority.HIGH,
    )
    plan = TaskDecomposer().decompose(root)
    by_type = {t.type: t for t in plan.atomic_tasks}

    assert by_type[TaskType.PLAN].priority == Priority.HIGH
    assert by_type[TaskType.CODE].priority == Priority.NORMAL
    assert by_type[TaskType.TEST].priority == Priority.NORMAL
    assert by_type[TaskType.REVIEW].priority == Priority.HIGH


def test_provider_budget_router_prefers_primary_provider_for_normal_code():
    task = Task(
        TaskType.CODE,
        TaskInput("Implement feature"),
        TaskContext("demo", ".", "main"),
        priority=Priority.NORMAL,
    )
    router = ProviderBudgetRouter()
    class _Choice:
        provider = "mistral"
    providers = router.preferred_providers(task, _Choice())
    assert providers[0] == "mistral"


def test_orchestrator_exposes_model_usage_snapshot():
    orchestrator = Orchestrator()
    sec = SecurityManager(SecurityPolicy(allow_shell=True, shell_allowlist=["npx @google/gemini-cli --prompt"]))

    orchestrator.attach_local_agent("planner-1", PlannerAgent("planner-1"), agent_type="planner", provider="openai")
    orchestrator.attach_local_agent("codex-main", CodexAgent("codex-main"), agent_type="codex", provider="openai")
    orchestrator.attach_local_agent("tester-1", TesterAgent("tester-1"), agent_type="tester", provider="openai")
    orchestrator.attach_local_agent("reviewer-1", ReviewerAgent("reviewer-1"), agent_type="reviewer", provider="openai")
    orchestrator.attach_local_agent("gemini-cli-1", GeminiCLIAgent("gemini-cli-1", sec), agent_type="external_ai", provider="google")

    result = orchestrator.submit_user_task({"type": "plan", "description": "Small feature", "priority": "normal"}, source="test")

    assert "model_usage" in result
    assert "history" in result["model_usage"]
    assert len(result["model_usage"]["history"]) >= 1
