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


def test_local_llm_bridge_auto_provisions_missing_container(monkeypatch):
    from ai_bridge.core.local_llm_bridge import LocalLLMBridge
    from types import SimpleNamespace

    bridge = LocalLLMBridge(container_name="ai-kernel-local", ollama_port=11434)
    calls: list[str] = []

    monkeypatch.setenv("AI_BRIDGE_LOCAL_LLM_AUTO_PROVISION", "true")
    monkeypatch.setattr(LocalLLMBridge, "container_exists", lambda self: False)
    monkeypatch.setattr(LocalLLMBridge, "_host_probe", lambda self: {"ok": True})
    monkeypatch.setattr(LocalLLMBridge, "is_model_downloaded", lambda self, model_name: True)
    monkeypatch.setattr(LocalLLMBridge, "_run", lambda self, args, check=False: SimpleNamespace(returncode=0, stdout="", stderr=""))

    monkeypatch.setattr("ai_bridge.core.local_llm_bridge.deploy_local_llm.ensure_container", lambda name: calls.append(f"ensure:{name}"))
    monkeypatch.setattr("ai_bridge.core.local_llm_bridge.deploy_local_llm.install_ollama", lambda name: calls.append(f"install:{name}"))
    monkeypatch.setattr("ai_bridge.core.local_llm_bridge.deploy_local_llm.start_service", lambda name: calls.append(f"start:{name}"))

    assert bridge.ensure_ready("qwen2.5:32b-instruct-q4_k_m") is True
    assert calls == ["ensure:ai-kernel-local", "install:ai-kernel-local", "start:ai-kernel-local"]
