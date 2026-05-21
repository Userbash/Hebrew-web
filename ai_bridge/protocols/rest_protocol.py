from __future__ import annotations

import json
from urllib import request

from ai_bridge.core.models import AgentHealth, AgentResult, AgentStatus, TaskStatus


class RestProtocol:
    def get_health(self, endpoint: str) -> AgentHealth:
        with request.urlopen(f"{endpoint.rstrip('/')}/health", timeout=10) as response:  # noqa: S310 - controlled endpoint
            data = json.loads(response.read().decode("utf-8"))
        return AgentHealth(
            agent_id=data["agent_id"],
            status=AgentStatus(data["status"]),
            capabilities=list(data["capabilities"]),
            active_tasks=int(data.get("active_tasks", 0)),
            queue_depth=int(data.get("queue_depth", 0)),
            avg_latency_ms=float(data.get("avg_latency_ms", 0)),
            success_rate=float(data.get("success_rate", 1.0)),
            last_error=data.get("last_error"),
            timestamp=data.get("timestamp"),
        )

    def post_task(self, endpoint: str, payload: dict, expected_agent_id: str | None = None) -> AgentResult:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(f"{endpoint.rstrip('/')}/task", data=body, headers={"Content-Type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=30) as response:  # noqa: S310 - controlled endpoint
            data = json.loads(response.read().decode("utf-8"))
        return AgentResult(
            task_id=data["task_id"],
            agent_id=data.get("agent_id") or expected_agent_id or data.get("assigned_agent", "external"),
            status=TaskStatus(data["status"]),
            output=data.get("output", {"summary": data.get("message", ""), "files_changed": [], "commands_run": [], "test_results": [], "diff": ""}),
            confidence=float(data.get("confidence", 0.5)),
            errors=list(data.get("errors", [])),
            next_recommendations=list(data.get("next_recommendations", [])),
        )
