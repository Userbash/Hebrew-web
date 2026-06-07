from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.message_bus import MessageBus
from ai_bridge.core.metrics import MetricsCollector
from ai_bridge.core.models import AgentHealth, AgentResult, AgentStatus, P2PMessage, P2PMessageType, TaskStatus


def test_registry_registration_capability_status_and_metrics_update():
    registry = AgentRegistry()
    agent = registry.register("tester-1", "tester", "local://tester", ["test", "ci"], limits={"max_active_tasks": 2})

    assert registry.get("tester-1") is agent
    assert registry.by_capability("test") == [agent]

    registry.update_health(AgentHealth(
        agent_id="tester-1",
        status=AgentStatus.DEGRADED,
        capabilities=["test"],
        active_tasks=1,
        queue_depth=2,
        avg_latency_ms=125.0,
        success_rate=0.75,
    ))

    assert agent.status == AgentStatus.DEGRADED
    assert agent.metrics.active_tasks == 1
    assert agent.metrics.queue_depth == 2
    assert agent.metrics.error_rate == 0.25


def test_metrics_collector_records_results_and_snapshot():
    registry = AgentRegistry()
    agent = registry.register("coder-1", "codex", "local://coder", ["code"])
    metrics = MetricsCollector()

    metrics.record_result(agent, AgentResult("task-1", "coder-1", TaskStatus.DONE, {"summary": "ok"}, 0.9), latency_ms=50)
    metrics.record_result(agent, AgentResult("task-2", "coder-1", TaskStatus.FAILED, {"summary": "bad"}, 0.2, ["failed"], []), latency_ms=150)
    snapshot = metrics.snapshot()

    assert snapshot["counters"] == {"task.done": 1, "task.failed": 1}
    assert snapshot["avg_latency_ms"]["coder-1"] == 100
    assert snapshot["agents"]["coder-1"]["success_rate"] == 0.5


def test_message_bus_transfers_context_payload_between_agents():
    bus = MessageBus()
    message = P2PMessage(
        task_id="task-context",
        from_agent="planner-1",
        to_agent="coder-1",
        message_type=P2PMessageType.CONTEXT_TRANSFER,
        payload={"context": {"files": ["app.py"], "criteria": ["tests pass"]}},
    )

    sent = bus.send_p2p(message)
    received = bus.receive_for_agent("coder-1")

    assert sent.ack_status.value == "sent"
    assert received is message
    assert received.payload["context"]["files"] == ["app.py"]
    assert [ack.ack_status.value for ack in bus.ack_history(message.message_id)] == ["sent", "received"]
