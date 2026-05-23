import pytest
from ai_bridge.core.message_bus import MessageBus
from ai_bridge.core.models import TaskPayload, encapsulate

def test_message_bus_send_envelope():
    bus = MessageBus()
    
    payload = TaskPayload("test", {}, {}, ["done"], "json", [])
    envelope = encapsulate(payload, {"target_agent": "agent-1", "max_hops": 2})
    
    # Hop 1
    ack = bus.send_envelope(envelope)
    assert ack.ack_status.value == "sent"
    assert bus.depth("agent.agent-1.inbox") == 1
    assert envelope.hop_count == 1
    
    received = bus.receive_for_agent("agent-1")
    assert received == envelope
    
    # Hop 2 - Exceeds max_hops
    ack2 = bus.send_envelope(envelope)
    assert ack2.ack_status.value == "failed"
    assert bus.depth("agent.agent-1.inbox") == 0
    assert len(bus.dead_letters) == 1
    assert bus.dead_letters[0] == envelope
