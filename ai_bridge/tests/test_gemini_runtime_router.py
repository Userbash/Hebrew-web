from __future__ import annotations

from ai_bridge.core.gemini_runtime_router import GeminiRuntimeRouter
from ai_bridge.core.models import Complexity, Task, TaskContext, TaskInput, TaskType


def _task(complexity: Complexity, session_id: str = "s1") -> Task:
    task = Task(
        TaskType.CODE,
        TaskInput("Implement feature with detailed changes"),
        TaskContext("demo", ".", "main"),
    )
    task.complexity = complexity
    task.session_id = session_id
    return task


def test_router_prefers_lite_for_low_complexity():
    router = GeminiRuntimeRouter()
    plan = router.build_plan(_task(Complexity.LOW), "small prompt")
    assert plan.models[0] == "gemini-2.5-flash-lite"


def test_router_prefers_pro_for_high_complexity():
    router = GeminiRuntimeRouter()
    plan = router.build_plan(_task(Complexity.HIGH), "large refactor task")
    assert plan.models[0] == "gemini-2.5-pro"


def test_router_tracks_session_usage():
    router = GeminiRuntimeRouter()
    task = _task(Complexity.MEDIUM, session_id="sess-usage")
    before = router.build_plan(task, "abc")
    router.register_usage(task, 10_000)
    after = router.build_plan(task, "abc")
    assert after.remaining_tokens < before.remaining_tokens
