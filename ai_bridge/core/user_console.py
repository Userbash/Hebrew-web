from __future__ import annotations

from dataclasses import dataclass, field

from .models import AgentRecord, Task


@dataclass(slots=True)
class UserConsole:
    events: list[str] = field(default_factory=list)

    def emit(self, stage: str, message: str) -> None:
        line = f"[{stage}] {message}"
        self.events.append(line)
        print(line)

    def agent_status(self, agent: AgentRecord, task: Task | None = None, progress: int = 0, stage: str = "idle") -> str:
        task_text = task.input.description if task else "нет активной задачи"
        line = (
            f"Агент: {agent.id}\n"
            f"Статус: {agent.status.value}\n"
            f"Задача: {task_text}\n"
            f"Модель: {agent.metrics.model_name}\n"
            f"Прогресс: {progress}%\n"
            f"Текущий этап: {stage}\n"
            f"Ошибки: {agent.disabled_reason or 'нет'}"
        )
        self.events.append(line)
        return line
