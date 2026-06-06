from __future__ import annotations

from ai_bridge.core.voice_listener_module import VoiceListenerModule


class _FakeAPI:
    def __init__(self) -> None:
        self.submissions: list[tuple[dict[str, object], str]] = []
        self.logs: list[tuple[str, str]] = []

    def log(self, level: str, message: str) -> None:
        self.logs.append((level, message))

    def get_module(self, name: str) -> object | None:
        return None

    def submit_user_task(self, payload: object, source: str = "user_input") -> dict[str, object]:
        assert isinstance(payload, dict)
        self.submissions.append((payload, source))
        return {"status": "done"}


def test_dispatch_to_core_submits_voice_payload() -> None:
    api = _FakeAPI()
    module = VoiceListenerModule()
    module._api = api

    module._dispatch_to_core("оркестратор проверь состояние оркестратора")

    assert api.submissions == [
        (
            {
                "message": "проверь состояние оркестратора",
                "description": "проверь состояние оркестратора",
                "source": "voice_input",
                "session_id": "voice",
            },
            "voice_listener",
        )
    ]


def test_dispatch_ignores_text_without_wake_word() -> None:
    api = _FakeAPI()
    module = VoiceListenerModule()
    module._api = api

    module._dispatch_to_core("Редактор субтитров А.Синецкая Корректор А.Егорова")

    assert api.submissions == []


def test_audio_recorder_prefers_configured_command(monkeypatch) -> None:
    module = VoiceListenerModule()
    monkeypatch.setenv("AI_BRIDGE_VOICE_RECORDER", "parec --format=s16le --rate=16000 --channels=1")

    assert module._audio_recorder_candidates(16000) == [["parec", "--format=s16le", "--rate=16000", "--channels=1"]]


def test_dispatch_accepts_fuzzy_wake_word() -> None:
    api = _FakeAPI()
    module = VoiceListenerModule()
    module._api = api

    module._dispatch_to_core("оркестратыр проверь какие модели подключены")

    assert api.submissions == [
        (
            {
                "message": "проверь какие модели подключены",
                "description": "проверь какие модели подключены",
                "source": "voice_input",
                "session_id": "voice",
            },
            "voice_listener",
        )
    ]
