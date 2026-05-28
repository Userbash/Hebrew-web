from __future__ import annotations

from .models import AgentResult, Task, TaskInput, TaskStatus, TaskType


class FeedbackLoop:
    def __init__(self, retry_limit: int = 3) -> None:
        self.retry_limit = retry_limit
        self._retries: dict[str, int] = {}

    def evaluate(self, task: Task, result: AgentResult) -> tuple[bool, Task | None]:
        if result.status == TaskStatus.DONE and result.confidence >= 0.7 and not result.errors:
            return True, None
        if task.type == TaskType.FIX or task.retry_count >= self.retry_limit:
            return False, None

        retry_key = task.parent_task_id or task.task_id
        count = self._retries.get(retry_key, 0)
        if count >= self.retry_limit:
            return False, None
        self._retries[retry_key] = count + 1
        fix_task = Task(
            type=TaskType.FIX,
            input=TaskInput(
                description=f"Fix failed task {task.task_id}: {'; '.join(result.errors) or result.output.get('summary', '')}",
                files=task.input.files,
                constraints=task.input.constraints,
                acceptance_criteria=task.input.acceptance_criteria,
            ),
            context=task.context,
            priority=task.priority,
            parent_task_id=task.parent_task_id or task.task_id,
            required_capability="fix",
            retry_count=count + 1,
        )
        return False, fix_task
