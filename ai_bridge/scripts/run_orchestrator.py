from __future__ import annotations

from ai_bridge.agents.codex_agent import CodexAgent
from ai_bridge.agents.planner_agent import PlannerAgent
from ai_bridge.agents.reviewer_agent import ReviewerAgent
from ai_bridge.agents.tester_agent import TesterAgent
from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.orchestrator import Orchestrator


def main() -> None:
    orchestrator = Orchestrator()
    orchestrator.attach_local_agent("planner-1", PlannerAgent("planner-1"), agent_type="planner", critical=True, model_name="gpt-planner", provider="openai")
    orchestrator.attach_local_agent("codex-main", CodexAgent("codex-main"), agent_type="codex", critical=True, model_name="gpt-coding-large", provider="openai")
    orchestrator.attach_local_agent("tester-1", TesterAgent("tester-1"), agent_type="tester", model_name="gpt-test-standard", provider="openai")
    orchestrator.attach_local_agent("reviewer-1", ReviewerAgent("reviewer-1"), agent_type="reviewer", model_name="gpt-review-large", provider="openai")
    task = Task(TaskType.PLAN, TaskInput("Create a small feature", acceptance_criteria=["tests pass"]), TaskContext("demo", ".", "main"))
    print(orchestrator.run(task))


if __name__ == "__main__":
    main()
