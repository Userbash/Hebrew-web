from __future__ import annotations
from dataclasses import dataclass

@dataclass(slots=True)
class TraceContext:
    trace_id: str
    workflow_id: str
    task_id: str
    parent_task_id: str | None = None
    agent_id: str | None = None
    user_id: str | None = None
