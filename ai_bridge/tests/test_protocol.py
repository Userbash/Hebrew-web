import pytest
from datetime import datetime, timedelta, UTC
from ai_bridge.core.models import (
    TaskPayload,
    TaskEnvelope,
    SecurityPolicy,
    encapsulate,
    decapsulate,
    ProtocolError
)

def test_encapsulate_decapsulate_success():
    payload = TaskPayload(
        objective="Test objective",
        input_data={"key": "value"},
        context={"repo": "test"},
        acceptance_criteria=["done"],
        expected_output_format="json"
    )
    
    envelope = encapsulate(payload, {
        "target_capability": "code",
        "priority": "high",
        "ttl": 3600
    })
    
    assert envelope.protocol_version == "1.0"
    assert envelope.target_capability == "code"
    assert envelope.payload == payload
    assert envelope.task_id is not None
    assert envelope.trace_id is not None
    
    decapsulated = decapsulate(envelope, ["code", "test"])
    assert decapsulated == payload

def test_decapsulate_unsupported_protocol():
    payload = TaskPayload(
        objective="Test", input_data={}, context={}, 
        acceptance_criteria=[], expected_output_format="text"
    )
    envelope = encapsulate(payload, {})
    envelope.protocol_version = "2.0"
    
    with pytest.raises(ProtocolError, match="Unsupported protocol version"):
        decapsulate(envelope, ["any"])

def test_decapsulate_deadline_exceeded():
    payload = TaskPayload(
        objective="Test", input_data={}, context={}, 
        acceptance_criteria=[], expected_output_format="text"
    )
    envelope = encapsulate(payload, {
        "deadline": datetime.now(UTC) - timedelta(minutes=5)
    })
    
    with pytest.raises(ProtocolError, match="Deadline exceeded"):
        decapsulate(envelope, ["any"])

def test_decapsulate_ttl_expired():
    payload = TaskPayload(
        objective="Test", input_data={}, context={}, 
        acceptance_criteria=[], expected_output_format="text"
    )
    envelope = encapsulate(payload, {"ttl": 0})
    
    with pytest.raises(ProtocolError, match="TTL expired"):
        decapsulate(envelope, ["any"])

def test_decapsulate_max_hops_exceeded():
    payload = TaskPayload(
        objective="Test", input_data={}, context={}, 
        acceptance_criteria=[], expected_output_format="text"
    )
    envelope = encapsulate(payload, {"max_hops": 3})
    envelope.hop_count = 3
    
    with pytest.raises(ProtocolError, match="Max hops \\(3\\) exceeded"):
        decapsulate(envelope, ["any"])

def test_decapsulate_capability_mismatch():
    payload = TaskPayload(
        objective="Test", input_data={}, context={}, 
        acceptance_criteria=[], expected_output_format="text"
    )
    envelope = encapsulate(payload, {"target_capability": "security"})
    
    with pytest.raises(ProtocolError, match="Agent lacks required capability: security"):
        decapsulate(envelope, ["code", "review"])
