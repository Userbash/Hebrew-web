from ai_bridge.core.feedback_loop import FeedbackLoop
from ai_bridge.core.models import AgentResult, Task, TaskContext, TaskInput, TaskStatus, TaskType


def test_feedback_creates_fix_task_on_failure():
    task = Task(TaskType.CODE, TaskInput("write code"), TaskContext("p", ".", "main"))
    result = AgentResult(task.task_id, "codex", TaskStatus.FAILED, {"summary": "failed", "files_changed": [], "commands_run": [], "test_results": [], "diff": ""}, 0.2, ["test failed"], [])

    ok, fix = FeedbackLoop(retry_limit=1).evaluate(task, result)

    assert not ok
    assert fix is not None
    assert fix.type == TaskType.FIX
    assert fix.required_capability == "fix"
