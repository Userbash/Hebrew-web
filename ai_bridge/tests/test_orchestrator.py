from ai_bridge.agents.codex_agent import CodexAgent
from ai_bridge.agents.planner_agent import PlannerAgent
from ai_bridge.agents.reviewer_agent import ReviewerAgent
from ai_bridge.agents.tester_agent import TesterAgent
from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskStatus, TaskType
from ai_bridge.core.orchestrator import Orchestrator


def test_full_cycle_plan_code_test_review_done():
    orchestrator = Orchestrator()
    orchestrator.attach_local_agent("planner-1", PlannerAgent("planner-1"))
    orchestrator.attach_local_agent("codex-main", CodexAgent("codex-main"))
    orchestrator.attach_local_agent("tester-1", TesterAgent("tester-1"))
    orchestrator.attach_local_agent("reviewer-1", ReviewerAgent("reviewer-1"))

    task = Task(TaskType.PLAN, TaskInput("Build feature", acceptance_criteria=["tests pass"]), TaskContext("demo", ".", "main"))
    result = orchestrator.run(task)

    assert result["status"] == "done"
    assert result["merged"]["status"] == "done"
    assert [item["status"] for item in result["results"]] == [TaskStatus.DONE.value] * 4
    assert any(event.startswith("[DONE]") for event in result["console"])
    assert "agents" in result["metrics"]
