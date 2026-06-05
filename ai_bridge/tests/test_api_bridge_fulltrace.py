from __future__ import annotations

from types import SimpleNamespace

from ai_bridge.core import api_bridge_module as api_module
from ai_bridge.core.api_bridge_module import APIBridgeModule, ChatRequest
from ai_bridge.core.task_submission_api import create_standard_task as real_create_standard_task


def _fake_standard_task(data):
    task = real_create_standard_task(data)
    task.task_id = "trace-task-123"
    return task


class _Control:
    def __init__(self) -> None:
        self.submissions: dict[str, dict[str, object]] = {}

    def task_status(self, task_id: str):
        return self.submissions.get(task_id)


class _Decision:
    task_id = "trace-task-123"

    def as_dict(self):
        return {"task_id": self.task_id, "route_mode": "orchestrator", "requires_orchestrator": True}


class _API:
    def __init__(self) -> None:
        self.control = _Control()
        self.live_trace_rows = []
        self.scheduler = SimpleNamespace(decisions=[_Decision()])

    def get_module(self, name):
        if name == "orchestrator_control":
            return self.control
        return None

    def submit_user_task(self, payload, source="user_input"):
        self.control.submissions["trace-task-123"] = {
            "task_id": "trace-task-123",
            "source": source,
            "description": payload["message"],
            "status": "done",
            "agent_id": "mistral-1",
            "orchestrator_source_of_truth": True,
        }
        self.live_trace_rows.append({"task_id": "trace-task-123", "router_agent": "mistral-1", "router_provider": "mistral"})
        return {"task_id": "trace-task-123", "status": "done", "results": [], "merged": {"summary": "ok"}}


def test_chat_fulltrace_reports_actual_task_path(monkeypatch):
    monkeypatch.setattr(api_module, "create_standard_task", _fake_standard_task)

    module = APIBridgeModule()
    module._api = _API()

    response = module._chat_trace_payload(
        ChatRequest(user_id="u1", message="trace me", session_id="sess-1", source="web_chat", provider="auto"),
        source_label="web_chat",
        provider_label="auto",
    )

    assert response["status"] == "completed"
    assert response["task"]["task_id"] == "trace-task-123"
    assert response["input"]["message"] == "trace me"
    assert response["normalized"]["message"] == "trace me"
    assert response["control"]["before"] is None
    assert response["control"]["after"]["status"] == "done"
    assert response["route"]["router_agent"] == "mistral-1"
    assert response["schedule"]["task_id"] == "trace-task-123"
    assert response["result"]["task_id"] == "trace-task-123"
