from __future__ import annotations

from .model_selector import ModelSelector
from .models import ExecutionPlan, Task, TaskInput, TaskType
from .task_router import CAPABILITY_BY_TASK_TYPE


class TaskDecomposer:
    def __init__(self, model_selector: ModelSelector | None = None) -> None:
        self.model_selector = model_selector or ModelSelector()

    def decompose(self, task: Task) -> ExecutionPlan:
        if task.type != TaskType.PLAN:
            self._decorate(task)
            return ExecutionPlan(root_task_id=task.task_id, atomic_tasks=[task])

        context = task.context
        description = task.input.description
        plan = Task(TaskType.PLAN, TaskInput(f"Plan: {description}", acceptance_criteria=["execution plan created"]), context, task.priority, parent_task_id=task.task_id)
        code = Task(TaskType.CODE, TaskInput(f"Implement: {description}", files=task.input.files, constraints=task.input.constraints, acceptance_criteria=task.input.acceptance_criteria), context, task.priority, parent_task_id=task.task_id, dependencies=[plan.task_id])
        test = Task(TaskType.TEST, TaskInput(f"Test: {description}", files=task.input.files, acceptance_criteria=["tests pass"]), context, task.priority, parent_task_id=task.task_id, dependencies=[code.task_id])
        review = Task(TaskType.REVIEW, TaskInput(f"Review: {description}", files=task.input.files, acceptance_criteria=["review pass"]), context, task.priority, parent_task_id=task.task_id, dependencies=[test.task_id])
        tasks = [plan, code, test, review]
        for atomic in tasks:
            self._decorate(atomic)
        return ExecutionPlan(root_task_id=task.task_id, atomic_tasks=tasks)

    def _decorate(self, task: Task) -> None:
        task.required_capability = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
        choice = self.model_selector.select(task)
        task.complexity = choice.complexity
        task.assigned_model = choice.model_name
        task.expected_output = task.expected_output or f"{task.type.value} result matching acceptance criteria"
