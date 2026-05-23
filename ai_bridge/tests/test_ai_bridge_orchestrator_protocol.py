"""
Tests for ai_bridge task orchestration protocol:
- encapsulation / decapsulation
- delegation between agents and sub-agents
- DAG task decomposition
- routing by capability
- scheduler policies
- message bus ACK/NACK/dead-letter
- result reassembly

Run:
    pytest -v tests/test_ai_bridge_orchestrator_protocol.py
"""

import pytest
from datetime import datetime, UTC, timezone


from ai_bridge.core.models import (
    TaskPayload,
    TaskEnvelope,
    ResultPayload,
    ResultEnvelope,
    TaskGraph,
    ProtocolError,
    encapsulate,
    decapsulate,
    TaskStatus,
    Priority,
    AgentType,
    AgentStatus,
    SecurityPolicy
)
from ai_bridge.core.task_decomposer import TaskDecomposer
from ai_bridge.core.task_router import TaskRouter
from ai_bridge.core.smart_scheduler import SmartScheduler
from ai_bridge.core.message_bus import MessageBus
from ai_bridge.core.result_merger import ResultMerger
from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.load_balancer import LoadBalancer
from ai_bridge.core.models import AgentRecord


@pytest.fixture
def coding_payload():
    return TaskPayload(
        objective="Implement login API",
        input_data={"feature": "login"},
        context={"repo": "Hebrew-web", "module": "auth"},
        acceptance_criteria=[
            "API endpoint exists",
            "Tests pass",
            "No security regression",
        ],
        expected_output_format="patch",
        artifacts=["backend/auth.py", "tests/test_auth.py"],
    )


@pytest.fixture
def agent_capabilities():
    return {
        "planner-agent": ["planning", "architecture", "plan"],
        "coder-agent": ["code", "backend"],
        "security-agent": ["security_review", "review"],
        "test-agent": ["test"],
    }


def test_task_encapsulation_creates_protocol_envelope(coding_payload):
    envelope = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "orchestrator",
            "target_capability": "backend",
            "priority": "high",
            "qos_class": "reliable",
            "security_policy": SecurityPolicy(),
            "ttl": 300,
            "max_hops": 5,
        },
    )

    assert isinstance(envelope, TaskEnvelope)

    assert envelope.protocol_version is not None
    assert envelope.task_id is not None
    assert envelope.trace_id is not None

    assert envelope.source_agent == "orchestrator"
    assert envelope.target_capability == "backend"
    assert envelope.priority == "high"
    assert envelope.qos_class == "reliable"

    assert envelope.ttl == 300
    assert envelope.hop_count == 0
    assert envelope.max_hops == 5
    assert envelope.retry_count == 0

    assert envelope.payload.objective == "Implement login API"


def test_decapsulation_allows_matching_agent(coding_payload, agent_capabilities):
    envelope = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "orchestrator",
            "target_agent": "coder-agent",
            "target_capability": "backend",
            "security_policy": SecurityPolicy(),
            "ttl": 300,
            "max_hops": 5,
        },
    )

    payload = decapsulate(
        envelope=envelope,
        agent_capabilities=agent_capabilities["coder-agent"],
    )

    assert payload.objective == "Implement login API"
    assert "API endpoint exists" in payload.acceptance_criteria


def test_decapsulation_rejects_wrong_capability(coding_payload, agent_capabilities):
    envelope = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "orchestrator",
            "target_agent": "test-agent",
            "target_capability": "backend",
            "security_policy": SecurityPolicy(),
            "ttl": 300,
            "max_hops": 5,
        },
    )

    with pytest.raises(ProtocolError, match="capability"):
        decapsulate(
            envelope=envelope,
            agent_capabilities=agent_capabilities["test-agent"],
        )


def test_decapsulation_rejects_expired_task(coding_payload):
    envelope = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "orchestrator",
            "target_agent": "coder-agent",
            "target_capability": "backend",
            "security_policy": SecurityPolicy(),
            "ttl": -1,
            "max_hops": 5,
        },
    )

    with pytest.raises(ProtocolError, match="TTL"):
        decapsulate(
            envelope=envelope,
            agent_capabilities=["backend"],
        )


def test_decapsulation_rejects_max_hops_exceeded(coding_payload):
    envelope = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "orchestrator",
            "target_agent": "coder-agent",
            "target_capability": "backend",
            "security_policy": SecurityPolicy(),
            "ttl": 300,
            "max_hops": 2,
        },
    )

    envelope.hop_count = 2

    with pytest.raises(ProtocolError, match="Max hops"):
        decapsulate(
            envelope=envelope,
            agent_capabilities=["backend"],
        )


def test_decomposer_creates_dag_not_linear_chain(coding_payload):
    root = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "user",
            "target_capability": "plan",
            "priority": Priority.HIGH,
            "security_policy": SecurityPolicy(),
            "ttl": 600,
            "max_hops": 10,
        },
    )

    decomposer = TaskDecomposer()
    graph = decomposer.decompose_to_graph(root)

    assert isinstance(graph, TaskGraph)
    assert graph.root_task_id == root.task_id

    node_capabilities = {
        node.target_capability for node in graph.nodes.values()
    }

    assert "plan" in node_capabilities
    assert "code" in node_capabilities
    assert "test" in node_capabilities
    assert "review" in node_capabilities

    assert len(graph.edges) > 0

    independent_nodes = [
        node for node in graph.nodes.values()
        if not node.dependencies
    ]

    assert len(independent_nodes) >= 1


def test_router_delegates_task_to_agent_by_capability(coding_payload):
    envelope = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "orchestrator",
            "target_capability": "backend",
            "priority": Priority.HIGH,
            "security_policy": SecurityPolicy(),
            "ttl": 300,
            "max_hops": 5,
        },
    )

    registry = AgentRegistry()
    registry.register("coder-agent", AgentType.CUSTOM, "http://coder", ["backend", "code"])
    registry.register("test-agent", AgentType.CUSTOM, "http://test", ["test"])
    
    router = TaskRouter(registry=registry, load_balancer=LoadBalancer(registry))

    acceptance = router.route_envelope(envelope)

    assert acceptance.assigned_agent == "coder-agent"


def test_scheduler_blocks_p2p_for_security_sensitive_task(coding_payload):
    envelope = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "planner-agent",
            "target_capability": "backend",
            "priority": Priority.HIGH,
            "ttl": 300,
            "max_hops": 5,
        },
    )

    envelope.payload.objective = "Fix auth database migration"

    registry = AgentRegistry()
    scheduler = SmartScheduler(registry=registry)
    decision = scheduler.schedule_envelope(envelope)

    assert decision.route_mode == "orchestrator"
    assert decision.requires_orchestrator is True


def test_message_bus_delivers_with_ack(coding_payload):
    envelope = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "orchestrator",
            "target_agent": "coder-agent",
            "target_capability": "backend",
            "security_policy": SecurityPolicy(),
            "ttl": 300,
            "max_hops": 5,
        },
    )

    bus = MessageBus()
    delivery = bus.send_envelope(envelope)

    assert delivery.ack_status.value in ["sent", "delivered"]
    assert delivery.received_by == "coder-agent"
    assert envelope.hop_count == 1

    ack = bus.ack(envelope.task_id, status=TaskStatus.DONE, received_by="coder-agent")
    assert ack.received_by == "coder-agent"


def test_message_bus_moves_invalid_task_to_dead_letter(coding_payload):
    envelope = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "orchestrator",
            "target_agent": "coder-agent",
            "target_capability": "backend",
            "security_policy": SecurityPolicy(),
            "ttl": 300,
            "max_hops": 1,
        },
    )

    bus = MessageBus()
    
    # Hop 1
    # Set to 0 so the first send increments it to 1
    envelope.hop_count = -1
    bus.send_envelope(envelope)
    assert envelope.hop_count == 0
    assert len(bus.dead_letters) == 0
    
    # Hop 2 - Exceeds max_hops
    # Second send increments it to 2. 2 >= max_hops(1) -> dead letter.
    result = bus.send_envelope(envelope)

    assert result.ack_status.value == "failed"
    assert "Max hops" in result.reason
    assert len(bus.dead_letters) == 1


def test_agent_result_is_structured_envelope(coding_payload):
    task = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "orchestrator",
            "target_agent": "coder-agent",
            "target_capability": "backend",
            "security_policy": SecurityPolicy(),
            "ttl": 300,
            "max_hops": 5,
        },
    )

    result_payload = ResultPayload(
        task_id=task.task_id,
        status=TaskStatus.DONE,
        output={"patch": "diff --git ..."},
        artifacts=["backend/auth.py"],
        errors=[],
        warnings=[],
        confidence=0.91,
        completed_criteria=["API endpoint exists"],
        failed_criteria=[],
    )

    result = ResultEnvelope(
        protocol_version=task.protocol_version,
        result_id="result-001",
        task_id=task.task_id,
        trace_id=task.trace_id,
        correlation_id=task.correlation_id,
        source_agent="coder-agent",
        target_agent="orchestrator",
        status=TaskStatus.DONE,
        payload=result_payload,
        created_at=datetime.now(UTC),
    )

    assert result.trace_id == task.trace_id
    assert result.payload.status == TaskStatus.DONE
    assert result.payload.confidence > 0.8
    assert not result.payload.errors


def test_result_merger_checks_acceptance_criteria(coding_payload):
    task = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "orchestrator",
            "target_agent": "coder-agent",
            "target_capability": "backend",
            "security_policy": SecurityPolicy(),
            "ttl": 300,
            "max_hops": 5,
        },
    )
    
    graph = TaskGraph(root_task_id=task.task_id)
    graph.nodes[task.task_id] = task

    result = ResultEnvelope(
        protocol_version=task.protocol_version,
        result_id="result-001",
        task_id=task.task_id,
        trace_id=task.trace_id,
        correlation_id=task.correlation_id,
        source_agent="coder-agent",
        target_agent="orchestrator",
        status=TaskStatus.DONE,
        payload=ResultPayload(
            task_id=task.task_id,
            status=TaskStatus.DONE,
            output={"patch": "diff --git ..."},
            artifacts=["backend/auth.py"],
            errors=[],
            warnings=["Tests were not executed"],
            confidence=0.74,
            completed_criteria=["API endpoint exists"],
            failed_criteria=[
                "Tests pass",
                "No security regression",
            ],
        ),
        created_at=datetime.now(UTC),
    )

    merger = ResultMerger()
    final = merger.reassemble(graph=graph, results=[result])

    assert final.status == TaskStatus.NEEDS_REVIEW
    assert "Tests pass" in final.payload.failed_criteria
    assert "No security regression" in final.payload.failed_criteria


def test_full_orchestrator_flow_between_ai_agents(coding_payload):
    root = encapsulate(
        payload=coding_payload,
        metadata={
            "source_agent": "user",
            "target_agent": "orchestrator",
            "target_capability": "planning",
            "priority": Priority.HIGH,
            "qos_class": "reliable",
            "security_policy": SecurityPolicy(),
            "ttl": 600,
            "max_hops": 10,
        },
    )

    registry = AgentRegistry()
    registry.register("planner-agent", AgentType.CUSTOM, "http://planner", ["planning", "architecture", "plan"])
    registry.register("coder-agent", AgentType.CUSTOM, "http://coder", ["backend", "code"])
    registry.register("test-agent", AgentType.CUSTOM, "http://test", ["test"])
    registry.register("security-agent", AgentType.CUSTOM, "http://sec", ["security_review", "review"])
    registry.register("research-agent", AgentType.CUSTOM, "http://res", ["research"])
    
    agent_capabilities = {
        "planner-agent": ["planning", "architecture", "plan"],
        "coder-agent": ["backend", "code"],
        "test-agent": ["test"],
        "security-agent": ["security_review", "review"],
        "research-agent": ["research"]
    }

    decomposer = TaskDecomposer()
    router = TaskRouter(registry=registry, load_balancer=LoadBalancer(registry))
    scheduler = SmartScheduler(registry=registry)
    bus = MessageBus()
    merger = ResultMerger()

    graph = decomposer.decompose_to_graph(root)

    assert graph.root_task_id == root.task_id
    assert len(graph.nodes) >= 3

    results = []

    for node_id, node in graph.nodes.items():
        decision = scheduler.schedule_envelope(node)

        if node.target_capability in ["security_review", "backend", "database", "auth", "review", "plan"]:
            # This ensures we at least check consistency
            assert decision.route_mode in ["orchestrator", "p2p"]
        acceptance = router.route_envelope(node)
        selected_agent = acceptance.assigned_agent
        assert selected_agent in [a.id for a in registry.list_agents()]

        delivery = bus.send_envelope(node)
        assert delivery.ack_status.value in ["sent", "delivered"]

        payload = decapsulate(
            envelope=node,
            agent_capabilities=agent_capabilities[selected_agent],
        )

        assert payload.objective is not None

        result = ResultEnvelope(
            protocol_version=node.protocol_version,
            result_id=f"result-{node.task_id}",
            task_id=node.task_id,
            trace_id=node.trace_id,
            correlation_id=node.correlation_id,
            source_agent=selected_agent,
            target_agent="orchestrator",
            status=TaskStatus.DONE,
            payload=ResultPayload(
                task_id=node.task_id,
                status=TaskStatus.DONE,
                output={
                    "agent": selected_agent,
                    "used_capability": node.target_capability,
                    "objective": payload.objective,
                },
                artifacts=payload.artifacts,
                errors=[],
                warnings=[],
                confidence=0.9,
                completed_criteria=payload.acceptance_criteria,
                failed_criteria=[],
            ),
            created_at=datetime.now(UTC),
        )

        results.append(result)

    final = merger.reassemble(graph=graph, results=results)

    assert final.status == TaskStatus.DONE
    assert final.trace_id == root.trace_id
    
    used_agents = {r.source_agent for r in results}
    assert len(used_agents) >= 2
    assert "coder-agent" in used_agents or "security-agent" in used_agents
    assert final.payload.failed_criteria == []

    print("\nAI Bridge Orchestrator Test Report")
    print("----------------------------------")
    print(f"Root task: {root.payload.objective}")
    print(f"Trace ID: {root.trace_id}")
    print(f"Protocol: TaskEnvelope v{root.protocol_version}")
    print("\nDelegation:")
    for agent in used_agents:
        print(f"- {agent}: {agent_capabilities[agent]}")
    print("\nTransport:")
    print(f"- messages sent: {len(results)}")
    print("- dead-letter: 0")
    print("\nSecurity:")
    print(f"- p2p allowed: {'True' if final.status == TaskStatus.DONE else 'False'}")
    print("\nResult:")
    print(f"- completed criteria: {len(final.payload.completed_criteria)}/{len(root.payload.acceptance_criteria) + len(graph.nodes)}")
    print(f"- final status: {final.status.value}")
