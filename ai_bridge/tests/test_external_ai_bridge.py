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
    monkeypatch.setattr(ExternalAIBridge, "resolve_antigravity_cli_command", staticmethod(lambda: ["agy"]))

    def fake_run(cmd, capture_output, text, timeout, env=None, cwd=None):
        calls.append(cmd)
        if len(calls) == 1:
            return SimpleNamespace(returncode=1, stdout="", stderr="RESOURCE_EXHAUSTED MODEL_CAPACITY_EXHAUSTED")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = bridge.run_antigravity_cli(_task(), "prompt", timeout_sec=30)

    assert result.ok is True
    assert len(calls) >= 2
    assert result.output == "ok"


def test_classify_error_timeout_types():
    assert ExternalAIBridge.classify_error("connection timed out") == "tcp_timeout"
    assert ExternalAIBridge.classify_error("gateway timeout 504") == "api_timeout"
    assert ExternalAIBridge.classify_error("resource_exhausted 429") == "quota_exhaustion"
    assert ExternalAIBridge.classify_error("invalid api key") == "auth_fail"


def test_bridge_treats_auth_prompt_output_as_failure(monkeypatch):
    bridge = ExternalAIBridge()
    monkeypatch.setattr(ExternalAIBridge, "resolve_antigravity_cli_command", staticmethod(lambda: ["agy"]))

    def fake_run(cmd, capture_output, text, timeout, env=None, cwd=None):
        return SimpleNamespace(returncode=0, stdout="Authentication required. Error: authentication timed out.", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = bridge.run_antigravity_cli(_task(), "prompt", timeout_sec=30)

    assert result.ok is False
    assert result.error_type == "auth_fail"
