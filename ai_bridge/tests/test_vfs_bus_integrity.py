import asyncio
import os
import json
import uuid
import pytest
from pathlib import Path
from datetime import datetime, UTC
import concurrent.futures

from ai_bridge.core.unified_vfs import UnifiedVFSModule, StateIntegrity, VFSNode
from ai_bridge.core.message_bus import MessageBus
from ai_bridge.core.models import P2PMessage, P2PMessageType, AckStatus, TaskEnvelope, TaskPayload, Priority, SecurityPolicy

def test_vfs_atomic_write_and_read(tmp_path):
    vfs = UnifiedVFSModule()
    vfs.storage_root = str(tmp_path / "vfs")
    vfs._root_path = Path(vfs.storage_root)
    vfs._artifacts_path = vfs._root_path / "artifacts"
    vfs._journal_path = vfs._root_path / "journal.wal"
    vfs._journal.journal_path = vfs._journal_path
    vfs.on_load(None) # type: ignore
    
    # Write
    content = {"status": "testing", "output": {"summary": "hello world"}}
    res = vfs.write_state("test/path/1", content, "agent_x")
    assert res is True
    
    # Read
    node = vfs.read_state("test/path/1")
    assert node is not None
    assert node.integrity == StateIntegrity.VALID
    assert node.content["output"]["summary"] == "hello world"

def test_vfs_artifacts_separation(tmp_path):
    vfs = UnifiedVFSModule()
    vfs.storage_root = str(tmp_path / "vfs")
    vfs._root_path = Path(vfs.storage_root)
    vfs._artifacts_path = vfs._root_path / "artifacts"
    vfs._journal_path = vfs._root_path / "journal.wal"
    vfs._journal.journal_path = vfs._journal_path
    vfs.on_load(None) # type: ignore
    
    large_text = "A" * 3000
    content = {"output": {"summary": large_text, "diff": "small diff"}}
    res = vfs.write_state("test/path/large", content, "agent_x")
    assert res is True
    
    # Check that it extracted the large file
    safe_path = "test_path_large"
    json_path = tmp_path / "vfs" / f"{safe_path}.json"
    
    with open(json_path, "r") as f:
        data = json.load(f)
        assert "$vfs_artifact" in data["content"]["output"]["summary"]
        assert "small diff" == data["content"]["output"]["diff"]
        
    # Read should inject it back
    node = vfs.read_state("test/path/large")
    assert node.content["output"]["summary"] == large_text

def test_vfs_corruption_recovery(tmp_path):
    vfs = UnifiedVFSModule()
    vfs.storage_root = str(tmp_path / "vfs")
    vfs._root_path = Path(vfs.storage_root)
    vfs._artifacts_path = vfs._root_path / "artifacts"
    vfs._journal_path = vfs._root_path / "journal.wal"
    vfs._journal.journal_path = vfs._journal_path
    vfs.on_load(None) # type: ignore
    
    vfs.write_state("test/corrupt", {"data": "ok"}, "agent")
    
    # Corrupt the file manually
    file_path = tmp_path / "vfs" / "test_corrupt.json"
    with open(file_path, "r") as f:
        data = json.load(f)
        
    data["content"]["data"] = "corrupted"
    
    with open(file_path, "w") as f:
        json.dump(data, f)
        
    # Clear memory cache so it reads from disk
    vfs._nodes.pop("test/corrupt", None)
        
    # Should detect corruption and rollback (delete and return None)
    node = vfs.read_state("test/corrupt")
    assert node is None
    assert not file_path.exists()

def test_concurrent_agent_write(tmp_path):
    vfs = UnifiedVFSModule()
    vfs.storage_root = str(tmp_path / "vfs")
    vfs._root_path = Path(vfs.storage_root)
    vfs._artifacts_path = vfs._root_path / "artifacts"
    vfs._journal_path = vfs._root_path / "journal.wal"
    vfs._journal.journal_path = vfs._journal_path
    vfs.on_load(None) # type: ignore

    def write_task(i):
        vfs.write_state("test/concurrent", {"id": i}, f"agent_{i}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(write_task, i) for i in range(50)]
        concurrent.futures.wait(futures)
        
    node = vfs.read_state("test/concurrent")
    assert node is not None
    assert node.integrity == StateIntegrity.VALID

def test_message_bus_unacked_replay():
    bus = MessageBus()
    
    msg = P2PMessage(
        task_id="task1",
        from_agent="A",
        to_agent="B",
        message_type=P2PMessageType.STATUS_UPDATE,
        requires_ack=True
    )
    
    bus.publish("agent.B.inbox", msg)
    consumed = bus.consume("agent.B.inbox")
    
    assert consumed == msg
    assert len(bus._unacked) == 1
    
    # Replay
    replayed = bus.replay_unacked()
    assert replayed == 1
    assert bus.depth("agent.B.inbox") == 1
    
    # Consume and Ack
    consumed2 = bus.consume("agent.B.inbox")
    assert consumed2 == msg
    bus.ack(msg.message_id, AckStatus.RECEIVED, "B")
    
    assert len(bus._unacked) == 0

def test_message_bus_dead_letter_envelope():
    bus = MessageBus()
    
    payload = TaskPayload(
        objective="Test", input_data={}, context={}, acceptance_criteria=[], expected_output_format="text"
    )
    
    env = TaskEnvelope(
        protocol_version="1",
        task_id="t1",
        parent_task_id=None,
        trace_id="tr1",
        correlation_id="c1",
        source_agent="A",
        target_agent="B",
        target_capability="code",
        priority=Priority.NORMAL,
        qos_class="normal",
        ttl=10,
        deadline=None,
        hop_count=9, # One hop away from DLQ if max=10
        max_hops=10,
        retry_count=0,
        max_retries=3,
        security_policy=SecurityPolicy(),
        context_scope="global",
        dependencies=[],
        payload=payload
    )
    
    bus.send_envelope(env)
    assert len(bus.dead_letters) == 1
    assert env in bus.dead_letters
