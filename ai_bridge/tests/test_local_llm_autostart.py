from __future__ import annotations

from types import SimpleNamespace

from ai_bridge.core.local_llm_module import LocalLLMModule
from ai_bridge.core.orchestrator import Orchestrator


class _Console:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def info(self, tag: str, message: str) -> None:
        self.messages.append((tag, message))

    def warning(self, tag: str, message: str) -> None:
        self.messages.append((tag, message))

    def emit(self, tag: str, message: str) -> None:
        self.messages.append((tag, message))


def test_autostart_local_llm_invokes_bridge(monkeypatch):
    module = LocalLLMModule(model_name="qwen2.5:32b-instruct-q4_k_m")
    bridge_calls: list[str] = []

    def fake_ensure_ready(model_name: str) -> bool:
        bridge_calls.append(model_name)
        return True

    monkeypatch.setattr(Orchestrator, "_local_llm_autostart_enabled", staticmethod(lambda: True))
    monkeypatch.setenv("TESTING", "false")

    orchestrator = Orchestrator.__new__(Orchestrator)
    orchestrator.console = _Console()
    orchestrator.module_manager = SimpleNamespace(get_module=lambda name: module)
    orchestrator.local_llm_bridge = SimpleNamespace(ensure_ready=fake_ensure_ready)
    orchestrator.log = Orchestrator.log.__get__(orchestrator, Orchestrator)

    Orchestrator._autostart_local_llm(orchestrator)

    assert bridge_calls == ["qwen2.5:32b-instruct-q4_k_m"]
    assert any("Autostart complete" in message for _, message in orchestrator.console.messages)
