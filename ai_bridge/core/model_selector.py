from __future__ import annotations

from dataclasses import dataclass

from .models import Complexity, Priority, Task, TaskType


@dataclass(slots=True)
class ModelChoice:
    model_name: str
    provider: str
    complexity: Complexity
    requires_secondary_review: bool = False


class ModelSelector:
    def classify(self, task: Task) -> Complexity:
        text = task.input.description.lower()
        if task.priority == Priority.CRITICAL or any(word in text for word in ("security", "secret", "production", "migration", "destructive")):
            return Complexity.CRITICAL
        if task.type in {TaskType.PLAN, TaskType.REVIEW} or any(word in text for word in ("architecture", "distributed", "debugging")):
            return Complexity.HIGH
        if task.type in {TaskType.CODE, TaskType.TEST, TaskType.FIX} or len(task.input.files) > 2:
            return Complexity.MEDIUM
        return Complexity.LOW

    def select(self, task: Task) -> ModelChoice:
        complexity = task.complexity or self.classify(task)
        if complexity == Complexity.LOW:
            return ModelChoice("local-small", "local", complexity)
        if complexity == Complexity.MEDIUM:
            return ModelChoice("gpt-coding-standard", "openai", complexity)
        if complexity == Complexity.HIGH:
            return ModelChoice("gpt-coding-large", "openai", complexity, requires_secondary_review=True)
        return ModelChoice("gpt-senior-secure", "openai", complexity, requires_secondary_review=True)
