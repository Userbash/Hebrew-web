from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Any
from .kernel_protocol import KernelAPI, KernelModule
from .session_memory import SessionMemory

logger = logging.getLogger(__name__)

class ColdBootModule(KernelModule):
    """
    Kernel Module for loading previous session memories on startup.
    Implements the 'Cold Auto-Start' functionality requested by the user.
    """
    name = "cold_boot"

    def __init__(self) -> None:
        self.api: KernelAPI | None = None
        self.booted = False

    def on_load(self, api: KernelAPI) -> None:
        self.api = api
        self.api.log("info", "ColdBootModule loaded. Ready for cold start.")

    def on_unload(self) -> None:
        self.api = None

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        """
        Check if the task is a request to trigger a cold start.
        """
        if hasattr(task, "description") and "COLD_START" in str(task.description).upper():
            self.trigger_cold_start()

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        pass

    def finalize(self) -> dict[str, Any]:
        return {"booted": self.booted}

    def trigger_cold_start(self) -> int:
        """
        Scans memory_store/ for the most recent previous run and loads it.
        """
        if self.api is None:
            return 0
        
        memory: SessionMemory = self.api.get_context("session_memory")
        if not memory:
            self.api.log("error", "SessionMemory not found in context.")
            return 0

        store_dir = Path("memory_store")
        if not store_dir.exists():
            return 0

        # Find all run directories, excluding the current one if possible
        # (Assuming current one is created by PersistentMemoryManager and we might be in it)
        # For simplicity, we just look for all run_* and sort by mtime
        runs = sorted(
            [d for d in store_dir.iterdir() if d.is_dir() and d.name.startswith("run_")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not runs:
            self.api.log("warn", "No previous runs found for cold start.")
            return 0

        # Pick the most recent one (that is NOT empty)
        target_run = None
        for run in runs:
            if (run / "memory_index.json").exists():
                target_run = run
                break
        
        if not target_run:
            self.api.log("warn", "No valid memory index found in previous runs.")
            return 0

        self.api.log("info", f"Initiating cold start from {target_run.name}...")
        count = memory.load_from_cold_storage(str(target_run))
        self.booted = True
        self.api.log("info", f"Cold start complete. Loaded {count} memories.")
        return count
