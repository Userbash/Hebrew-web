from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from ai_bridge.core.orchestration_config import RiskLevel

@dataclass(slots=True)
class AuditEvent:
    action: str
    task_id: str
    risk_level: RiskLevel
    approved_by: Optional[str] = None
    auto_approved: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: dict[str, Any] = field(default_factory=dict)

class AuditTrail:
    def __init__(self):
        self.logs: list[AuditEvent] = []

    def log(self, event: AuditEvent):
        self.logs.append(event)
        # Log to system console/file as well
        print(f"[AUDIT] {event.timestamp.isoformat()} | {event.task_id} | {event.action} | Risk: {event.risk_level.value} | Auto: {event.auto_approved}")
