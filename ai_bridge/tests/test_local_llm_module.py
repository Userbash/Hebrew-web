from __future__ import annotations

from ai_bridge.core.local_llm_module import LocalLLMModule


class _Response:
    def __init__(self, status_code: int = 200, payload: dict[str, object] | None = None, content: bytes = b"{}"):
        self.status_code = status_code
        self._payload = payload or {}
        self.content = content

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"status={self.status_code}")

    def json(self) -> dict[str, object]:
        return self._payload


class _Api:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def log(self, level: str, message: str) -> None:
        self.messages.append((level, message))

    def get_context(self, key: str):
        return None

    def emit_event(self, event_name: str, payload: dict[str, object]) -> None:
        return None

    def query_module_state(self, module_name: str, key: str):
        return None

    def get_memory(self):
        return None


def test_local_llm_module_reports_ready_when_model_is_available(monkeypatch):
    def fake_get(url: str, timeout: float):
        assert url == "http://127.0.0.1:11434/api/tags"
        assert timeout == 1.0
        return _Response(payload={"models": [{"name": "qwen2.5:32b-instruct-q4_k_m"}]})

    monkeypatch.setattr("ai_bridge.core.local_llm_module.requests.get", fake_get)

    module = LocalLLMModule()
    api = _Api()
    module.on_load(api)

    assert module.finalize()["status"] == "ready"
    assert module.finalize()["service_reachable"] is True
    assert module.finalize()["model_present"] is True
    assert any("reachable and ready" in msg for _, msg in api.messages)


def test_local_llm_module_reports_degraded_when_model_missing(monkeypatch):
    monkeypatch.setattr(
        "ai_bridge.core.local_llm_module.requests.get",
        lambda url, timeout: _Response(payload={"models": [{"name": "llama3:latest"}]}),
    )

    module = LocalLLMModule()
    result = module.check_health()

    assert result["ok"] is True
    assert result["model_present"] is False
    assert module.finalize()["status"] == "degraded"
