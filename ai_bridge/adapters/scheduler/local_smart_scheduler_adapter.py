from __future__ import annotations
from typing import Any
from ai_bridge.core.smart_scheduler import SmartScheduler

class LocalSmartSchedulerAdapter:
    def __init__(self, scheduler: SmartScheduler) -> None:
        self.scheduler = scheduler
    def schedule_task(self, task: Any) -> dict[str, Any]:
        d = self.scheduler.schedule(task)
        return {"route_mode": d.route_mode, "target_agent": d.target_agent, "reason": d.reason}
    def enqueue_retry(self, task: Any, reason: str) -> None:
        _ = (task, reason)
