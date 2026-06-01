from __future__ import annotations
import os
class APSchedulerBackend:
    def __init__(self) -> None:
        self.enabled = os.getenv("AI_BRIDGE_ENABLE_APSCHEDULER", "false").lower() in {"1","true","yes","on"}
    def schedule_task(self, task):
        return {"scheduled": self.enabled, "backend": "apscheduler", "task": getattr(task, "task_id", "unknown")}
    def enqueue_retry(self, task, reason: str) -> None:
        _ = (task, reason)
