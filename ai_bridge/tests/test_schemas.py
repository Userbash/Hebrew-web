import pytest
from pydantic import ValidationError
from uuid import uuid4
from ai_bridge.core.models import Task, AgentHealth, TaskResult

def test_task_schema_validation():
    """
    TDD: Verify that the Task model correctly validates input.
    """
    valid_task_data = {
        "task_id": str(uuid4()),
        "type": "code",
        "priority": "normal",
        "input": {
            "description": "Implement a new feature",
            "files": ["src/main.py"]
        },
        "context": {
            "project": "test-project"
        }
    }
    task = Task(**valid_task_data)
    assert task.type.value == "code"
    
    # Test invalid type
    with pytest.raises(ValidationError):
        Task(**{**valid_task_data, "type": "invalid-type"})

def test_agent_health_schema():
    """
    TDD: Verify the AgentHealth model.
    """
    health_data = {
        "agent_id": "agent-1",
        "status": "ready",
        "capabilities": ["code", "test"],
        "active_tasks": 0,
        "success_rate": 1.0,
        "timestamp": "2026-06-07T12:00:00Z"
    }
    health = AgentHealth(**health_data)
    assert health.status.value == "ready"
    assert "code" in health.capabilities

def test_task_result_schema():
    """
    TDD: Verify the TaskResult model.
    """
    result_data = {
        "task_id": str(uuid4()),
        "agent_id": "agent-1",
        "status": "done",
        "output": {
            "summary": "Completed successfully",
            "files_changed": ["main.py"]
        },
        "confidence": 0.95
    }
    result = TaskResult(**result_data)
    assert result.status.value == "done"
    assert result.confidence == 0.95
