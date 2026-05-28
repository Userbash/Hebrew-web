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


def test_feedback_loop_does_not_recurse_fix_tasks():
    from ai_bridge.core.feedback_loop import FeedbackLoop
    from ai_bridge.core.models import AgentResult, Priority, Task, TaskContext, TaskInput, TaskStatus, TaskType

    feedback = FeedbackLoop(retry_limit=1)
    task = Task(TaskType.PLAN, TaskInput("broken"), TaskContext("demo", ".", "main"), priority=Priority.NORMAL)
    result = AgentResult(task.task_id, "agent", TaskStatus.FAILED, {"summary": "bad"}, 0.1, ["bad"], [])

    ok, fix_task = feedback.evaluate(task, result)
    assert not ok
    assert fix_task is not None
    assert fix_task.parent_task_id == task.task_id
    assert fix_task.retry_count == 1

    fix_result = AgentResult(fix_task.task_id, "agent", TaskStatus.FAILED, {"summary": "still bad"}, 0.1, ["bad"], [])
    ok, nested_fix = feedback.evaluate(fix_task, fix_result)
    assert not ok
    assert nested_fix is None
