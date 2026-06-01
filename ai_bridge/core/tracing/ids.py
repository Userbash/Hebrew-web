from __future__ import annotations
from uuid import uuid4

def new_trace_id() -> str:
    return str(uuid4())

def new_workflow_id() -> str:
    return str(uuid4())
