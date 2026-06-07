from ai_bridge.agents.base_agent import BaseAgent
from ai_bridge.agents.planner_agent import PlannerAgent
from ai_bridge.agents.reviewer_agent import ReviewerAgent
from ai_bridge.agents.tester_agent import TesterAgent
from ai_bridge.core.models import AgentResult, Task, TaskContext, TaskInput, TaskStatus, TaskType
from ai_bridge.core.orchestrator import Orchestrator


class LocalCodeAgent(BaseAgent):
    def __init__(self, agent_id: str = "code-1") -> None:
        super().__init__(agent_id, ["code", "fix", "refactor"])

    def run(self, task: Task, memory_context: dict | None = None):
        return self.result(task, "Implemented requested code changes.")


class FailingCodeAgent(BaseAgent):
    def __init__(self, agent_id: str = "code-failing") -> None:
        super().__init__(agent_id, ["code"])

    def run(self, task: Task, memory_context: dict | None = None):
        return self.result(task, "Implementation failed tests.", TaskStatus.FAILED, confidence=0.2, errors=["tests failed"])


class FixAgent(BaseAgent):
    def __init__(self, agent_id: str = "fix-1") -> None:
        super().__init__(agent_id, ["fix"])

    def run(self, task: Task, memory_context: dict | None = None):
        return self.result(task, "Fixed failed implementation and reran tests.")


class ResearchAgent(BaseAgent):
    def __init__(self, agent_id: str = "research-1") -> None:
        super().__init__(agent_id, ["research"])

    def run(self, task: Task, memory_context: dict | None = None):
        return self.result(task, "Collected supporting context and references.")


class DocsAgent(BaseAgent):
    def __init__(self, agent_id: str = "docs-1") -> None:
        super().__init__(agent_id, ["docs"])

    def run(self, task: Task, memory_context: dict | None = None):
        return self.result(task, "Prepared required documentation updates.")


def _orchestrator_with_agents(code_agent: BaseAgent | None = None, fix_agent: BaseAgent | None = None) -> Orchestrator:
    orchestrator = Orchestrator()
    orchestrator.attach_local_agent("planner-1", PlannerAgent("planner-1"))
    orchestrator.attach_local_agent("code-main", code_agent or LocalCodeAgent("code-main"))
    orchestrator.attach_local_agent("tester-1", TesterAgent("tester-1"))
    orchestrator.attach_local_agent("reviewer-1", ReviewerAgent("reviewer-1"))
    orchestrator.attach_local_agent("research-1", ResearchAgent("research-1"))
    orchestrator.attach_local_agent("docs-1", DocsAgent("docs-1"))
    if fix_agent:
        orchestrator.attach_local_agent("fix-1", fix_agent)
    return orchestrator


def test_full_cycle_plan_code_test_review_done():
    orchestrator = _orchestrator_with_agents()

    task = Task(TaskType.PLAN, TaskInput("Build feature", acceptance_criteria=["tests pass"]), TaskContext("demo", ".", "main"))
    result = orchestrator.run(task)

    assert result["status"] == "done"
    assert result["merged"]["status"] == "done"
    assert result["results"]
    assert all(item["status"] == "done" for item in result["results"])
    assert any(event.startswith("[DONE]") for event in result["console"])
    assert "agents" in result["metrics"]


def test_full_cycle_delegates_failed_code_to_fix_agent_and_finishes():
    orchestrator = _orchestrator_with_agents(FailingCodeAgent("code-main"), FixAgent("fix-1"))

    task = Task(TaskType.PLAN, TaskInput("Build feature with a failing first implementation", acceptance_criteria=["tests pass"]), TaskContext("demo", ".", "main"))
    result = orchestrator.run(task)

    assert result["status"] == "done"
    assert any(item["agent_id"] == "fix-1" and item["status"] == "done" for item in result["results"])
    assert any(event.startswith("[FIX]") for event in result["console"])
    assert any(row.get("router_agent") == "fix-1" for row in result["live_trace"])


def test_feedback_loop_does_not_recurse_fix_tasks():
    from ai_bridge.core.feedback_loop import FeedbackLoop
    from ai_bridge.core.models import Priority

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
