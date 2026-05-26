from __future__ import annotations

from ai_bridge.agents.codex_agent import CodexAgent
from ai_bridge.agents.planner_agent import PlannerAgent
from ai_bridge.agents.reviewer_agent import ReviewerAgent
from ai_bridge.agents.tester_agent import TesterAgent
from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.orchestrator import Orchestrator


def test_modprobe_style_load_unload():
    orchestrator = Orchestrator()

    assert "ai_activity" in orchestrator.loaded_kernel_modules()
    assert "orchestrator_control" in orchestrator.loaded_kernel_modules()

    orchestrator.unload_kernel_module("ai_activity")
    assert "ai_activity" not in orchestrator.loaded_kernel_modules()

    orchestrator.load_kernel_module("ai_activity")
    assert "ai_activity" in orchestrator.loaded_kernel_modules()


def test_ai_activity_in_final_result():
    orchestrator = Orchestrator()
    orchestrator.attach_local_agent("planner-1", PlannerAgent("planner-1"))
    orchestrator.attach_local_agent("codex-main", CodexAgent("codex-main"))
    orchestrator.attach_local_agent("tester-1", TesterAgent("tester-1"))
    orchestrator.attach_local_agent("reviewer-1", ReviewerAgent("reviewer-1"))

    task = Task(TaskType.PLAN, TaskInput("Build feature", acceptance_criteria=["tests pass"]), TaskContext("demo", ".", "main"))
    result = orchestrator.run(task)

    assert "kernel_modules" in result
    assert "ai_activity" in result
    assert "ai_activity" in result["module_state"]
    assert result["ai_activity"]["total_tasks"] >= 1


def test_submit_user_task_uses_orchestrator_as_source_of_truth():
    orchestrator = Orchestrator()
    orchestrator.attach_local_agent("planner-1", PlannerAgent("planner-1"))
    orchestrator.attach_local_agent("codex-main", CodexAgent("codex-main"))
    orchestrator.attach_local_agent("tester-1", TesterAgent("tester-1"))
    orchestrator.attach_local_agent("reviewer-1", ReviewerAgent("reviewer-1"))

    orchestrator.submit_user_task({"type": "plan", "description": "Build feature", "acceptance_criteria": ["tests pass"]}, source="test")
    snapshot = orchestrator.monitoring_snapshot()

    assert snapshot["source_of_truth"] == "orchestrator"
    assert snapshot["submitted_total"] >= 1
    assert snapshot["finished_total"] >= 1
    assert isinstance(snapshot["tasks"], dict)
