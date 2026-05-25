from __future__ import annotations

import subprocess
from types import SimpleNamespace

from ai_bridge.core.external_ai_bridge import ExternalAIBridge
from ai_bridge.core.models import Complexity, Task, TaskContext, TaskInput, TaskType


def _task() -> Task:
    task = Task(TaskType.CODE, TaskInput("Implement feature"), TaskContext("demo", ".", "main"))
    task.complexity = Complexity.MEDIUM
    task.session_id = "sess-bridge"
    return task


def test_bridge_fallbacks_to_next_model_on_capacity_error(monkeypatch):
    bridge = ExternalAIBridge()
    calls: list[list[str]] = []

    def fake_run(cmd, capture_output, text, timeout):
        calls.append(cmd)
        if len(calls) == 1:
            return SimpleNamespace(returncode=1, stdout="", stderr="RESOURCE_EXHAUSTED MODEL_CAPACITY_EXHAUSTED")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = bridge.run_gemini_cli(_task(), "prompt", timeout_sec=30)

    assert result.ok is True
    assert len(calls) >= 2
    assert result.output == "ok"
