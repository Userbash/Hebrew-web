from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any
from pathlib import Path

from .orchestrator import Orchestrator
from .task_submission_api import create_standard_task, normalize_user_payload

logger = logging.getLogger(__name__)


class TaskListener:
    def __init__(self, orchestrator: Orchestrator, queue_path: str = ".agent/bridge_queue.json", result_dir: str = ".agent/bridge_results", poll_interval_sec: float = 2.0):
        self.orchestrator = orchestrator
        self.queue_path = queue_path
        self.result_dir = result_dir
        self.poll_interval_sec = poll_interval_sec
        self.running = False

    def _extract_task_payloads(self, payload: Any) -> list[dict[str, Any]]:
        normalized = normalize_user_payload(payload)
        if not normalized:
            return []

        raw_tasks = normalized.get("tasks")
        if isinstance(raw_tasks, list):
            tasks: list[dict[str, Any]] = []
            for item in raw_tasks:
                item_normalized = normalize_user_payload(item)
                if item_normalized:
                    tasks.append(item_normalized)
            return tasks

        return [normalized]


    def _write_result_file(self, task_id: str, result: dict[str, Any]) -> None:
        Path(self.result_dir).mkdir(parents=True, exist_ok=True)
        out = Path(self.result_dir) / f"{task_id}.json"
        with out.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=True)

    async def _process_payload(self, payload: Any) -> None:
        task_payloads = self._extract_task_payloads(payload)
        if not task_payloads:
            return

        for raw_task in task_payloads:
            task = create_standard_task(raw_task)
            logger.info("[LISTENER] Processing task: %s", task.task_id)
            result_data = self.orchestrator.submit_user_task(raw_task, source="queue")
            self._write_result_file(task.task_id, result_data)
            logger.info(
                "[LISTENER] Task %s completed with status %s",
                task.task_id,
                result_data.get("status", "unknown"),
            )

    async def start(self) -> None:
        self.running = True
        logger.info("[LISTENER] Background task listener started")
        while self.running:
            try:
                if os.path.exists(self.queue_path):
                    with open(self.queue_path, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                    await self._process_payload(payload)
                    os.remove(self.queue_path)
            except Exception as e:
                logger.exception("[LISTENER] Error while processing queue: %s", e)

            await asyncio.sleep(self.poll_interval_sec)

    async def submit_user_input(self, user_input: str) -> dict[str, Any]:
        """Direct intake path for interactive environments without file queue."""
        task_payload = normalize_user_payload(user_input)
        result = self.orchestrator.submit_user_task(task_payload, source="direct_input")
        maybe_id = task_payload.get("task_id") if isinstance(task_payload, dict) else None
        if isinstance(maybe_id, str) and maybe_id:
            self._write_result_file(maybe_id, result)
        return result
