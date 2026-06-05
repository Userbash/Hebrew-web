from __future__ import annotations

import subprocess
from types import SimpleNamespace

from ai_bridge.agents.gemini_cli_agent import GeminiCLIAgent
from ai_bridge.core.external_ai_bridge import ExternalAIBridge
from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskStatus, TaskType
from ai_bridge.core.security import SecurityManager, SecurityPolicy


def _task() -> Task:
    return Task(
        TaskType.CODE,
        TaskInput("Implement feature"),
        TaskContext("demo", ".", "main"),
    )


def _agent() -> GeminiCLIAgent:
    policy = SecurityPolicy(allow_shell=True, shell_allowlist=["gemini --prompt", "npx @google/gemini-cli --prompt"])
    return GeminiCLIAgent("gemini-cli-1", SecurityManager(policy))


def test_gemini_cli_success_uses_non_interactive(monkeypatch):
    agent = _agent()
    captured = {}

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        captured["timeout"] = timeout
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(ExternalAIBridge, "resolve_gemini_cli_command", staticmethod(lambda: ["gemini"]))
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = agent.run(_task())

    assert result.status == TaskStatus.DONE
    assert captured["cmd"][:3] == ["gemini", "--prompt", "Implement feature"]
    assert captured["timeout"] == 120


def test_gemini_cli_timeout_returns_failed(monkeypatch):
    agent = _agent()

    def fake_run(cmd, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = agent.run(_task())

    assert result.status == TaskStatus.FAILED
    assert "timed out" in result.output["summary"].lower()
    assert agent.active_tasks == 0
