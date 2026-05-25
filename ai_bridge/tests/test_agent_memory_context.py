from __future__ import annotations

from ai_bridge.agents.base_agent import BaseAgent
from ai_bridge.core.models import AgentResult, Task, TaskContext, TaskInput, TaskStatus, TaskType
from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.core.session_memory import MemoryScope


class MemoryEchoAgent(BaseAgent):
    def __init__(self, agent_id: str = "memory-echo") -> None:
        super().__init__(agent_id, ["code"])
        self.last_context: dict | None = None

    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        self.last_context = memory_context or {}
        return self.result(task, f"context_keys={sorted((memory_context or {}).keys())}", TaskStatus.DONE)


def _task() -> Task:
    return Task(
        type=TaskType.CODE,
        input=TaskInput(description="x"),
        context=TaskContext(project="p", repo_path=".", branch="main"),
    )


def test_orchestrator_passes_cached_memory_context_to_agent():
    orchestrator = Orchestrator()
    agent = MemoryEchoAgent("memory-echo")
    orchestrator.attach_local_agent("memory-echo", agent, agent_type="codex")

    task = _task()
    task.required_capability = "code"
    task.memory_scope = "session"
    task.session_id = "sess-123"
    task.memory_keys = ["project_tree"]

    orchestrator.session_memory.set(MemoryScope.SESSION, "sess-123", "project_tree", {"files": ["a.ts"]})

    result = orchestrator.run_task(task)

    assert result.status == TaskStatus.DONE
    assert agent.last_context == {"project_tree": {"files": ["a.ts"]}}


def test_orchestrator_writes_last_result_to_memory():
    orchestrator = Orchestrator()
    agent = MemoryEchoAgent("memory-echo")
    orchestrator.attach_local_agent("memory-echo", agent, agent_type="codex")

    task = _task()
    task.required_capability = "code"
    task.memory_scope = "task"

    result = orchestrator.run_task(task)
    assert result.status == TaskStatus.DONE

    stored = orchestrator.session_memory.get(MemoryScope.TASK, task.task_id, "last_result")
    assert stored is not None
    assert stored["task_id"] == task.task_id
