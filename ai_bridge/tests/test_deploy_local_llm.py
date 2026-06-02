from __future__ import annotations

from types import SimpleNamespace

from ai_bridge.scripts import deploy_local_llm


def test_run_command_invokes_subprocess(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, check, capture_output, text):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(deploy_local_llm.subprocess, "run", fake_run)

    result = deploy_local_llm.run_command(["distrobox", "list", "--no-color"])

    assert result.returncode == 0
    assert calls == [["distrobox", "list", "--no-color"]]


def test_verify_ready_checks_local_ollama_endpoint(monkeypatch):
    recorded: list[list[str]] = []

    def fake_run(cmd, check, capture_output, text):
        recorded.append(cmd)
        return SimpleNamespace(returncode=0, stdout="True\n", stderr="")

    monkeypatch.setattr(deploy_local_llm.subprocess, "run", fake_run)
    monkeypatch.setattr(deploy_local_llm, "MODEL_NAME", "qwen2.5:32b-instruct-q4_k_m")
    monkeypatch.setattr(deploy_local_llm, "OLLAMA_PORT", "11434")

    assert deploy_local_llm.verify_ready() is True
    assert recorded[0][0] == "python3"
