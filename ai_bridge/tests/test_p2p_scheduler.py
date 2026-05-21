from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.message_bus import MessageBus
from ai_bridge.core.models import (
    AckStatus,
    AgentStatus,
    Complexity,
    P2PMessage,
    P2PMessageType,
    Priority,
    ReadinessLevel,
    Task,
    TaskContext,
    TaskInput,
    TaskType,
)
from ai_bridge.core.smart_scheduler import SmartScheduler


def make_task(task_type=TaskType.TEST, priority=Priority.NORMAL, description="rerun failed local test"):
    return Task(task_type, TaskInput(description), TaskContext("demo", ".", "main"), priority=priority)


def test_scheduler_allows_p2p_for_low_risk_local_task():
    registry = AgentRegistry()
    agent = registry.register("tester-1", "tester", "local://tester", ["test"], limits={"max_active_tasks": 4})
    agent.status = AgentStatus.IDLE
    scheduler = SmartScheduler(registry)

    decision = scheduler.schedule(make_task())

    assert decision.route_mode == "p2p"
    assert decision.assigned_agent == "tester-1"
    assert decision.requires_orchestrator is False
    assert decision.readiness == ReadinessLevel.HOT
    assert decision.task_score > 0


def test_scheduler_escalates_critical_security_or_api_task_to_orchestrator():
    registry = AgentRegistry()
    registry.register("codex-main", "codex", "local://codex", ["code", "fix"], critical=True)
    scheduler = SmartScheduler(registry)
    task = Task(
        TaskType.CODE,
        TaskInput("Change auth API and database schema", constraints=["requires audit log"]),
        TaskContext("demo", ".", "main"),
        priority=Priority.CRITICAL,
        complexity=Complexity.CRITICAL,
        required_capability="code",
    )

    decision = scheduler.schedule(task)

    assert decision.route_mode == "orchestrator"
    assert decision.requires_orchestrator is True
    assert decision.assigned_agent == "codex-main"


def test_scheduler_skips_overloaded_agents_and_uses_ready_fallback():
    registry = AgentRegistry()
    overloaded = registry.register("tester-hot", "tester", "local://hot", ["test"], limits={"max_active_tasks": 1})
    overloaded.status = AgentStatus.OVERLOADED
    fallback = registry.register("tester-standby", "tester", "local://standby", ["test"], limits={"max_active_tasks": 2})
    fallback.status = AgentStatus.STANDBY
    scheduler = SmartScheduler(registry)

    decision = scheduler.schedule(make_task())

    assert decision.assigned_agent == "tester-standby"
    assert decision.readiness == ReadinessLevel.WARM


def test_p2p_message_ack_and_relay_trace():
    bus = MessageBus()
    message = P2PMessage(
        task_id="task-123",
        from_agent="tester_agent",
        to_agent="coder_agent",
        message_type=P2PMessageType.TEST_FAILED,
        priority="high",
        payload={"failed_tests": ["test_auth_login"], "error": "Expected 200, got 401"},
    )

    sent_ack = bus.relay_p2p(message, nearest_peer="reviewer_agent")
    received = bus.receive_for_agent("coder_agent")
    bus.ack(message.message_id, AckStatus.ACCEPTED, "coder_agent")

    assert sent_ack.ack_status == AckStatus.SENT
    assert received is message
    assert message.delivery_mode == "p2p_relay"
    assert message.route == ["tester_agent", "reviewer_agent", "coder_agent"]
    assert [ack.ack_status for ack in bus.ack_history(message.message_id)] == [
        AckStatus.SENT,
        AckStatus.RECEIVED,
        AckStatus.ACCEPTED,
    ]


def test_scheduler_escalation_policy_after_retry_limit():
    registry = AgentRegistry()
    registry.register("coder-1", "codex", "local://coder", ["fix"])
    scheduler = SmartScheduler(registry)
    task = make_task(TaskType.FIX, Priority.NORMAL, "local style fix")

    assert scheduler.should_escalate(task, retry_count=1) is False
    assert scheduler.should_escalate(task, retry_count=4) is True
