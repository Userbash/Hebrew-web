from __future__ import annotations

from ai_bridge.agents.gemini_agent import GeminiAgent
from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskStatus, TaskType


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeClient:
    def __init__(self) -> None:
        self.last_prompt = None

    def generate_content(self, prompt: str):
        self.last_prompt = prompt
        return _FakeResponse("ok")


def _task() -> Task:
    return Task(
        TaskType.CODE,
        TaskInput("Implement from description"),
        TaskContext("demo", ".", "main"),
    )


def test_gemini_agent_uses_task_description_prompt(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    agent = GeminiAgent("gemini-1")
    fake = _FakeClient()
    agent._client = fake
    agent._init_error = None

    result = agent.run(_task())

    assert result.status == TaskStatus.DONE
    assert fake.last_prompt == "Implement from description"


def test_gemini_agent_returns_failed_when_not_configured(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    agent = GeminiAgent("gemini-1")
    agent._client = None
    agent._init_error = "missing key"

    result = agent.run(_task())

    assert result.status == TaskStatus.FAILED
    assert "missing key" in " ".join(result.errors)
