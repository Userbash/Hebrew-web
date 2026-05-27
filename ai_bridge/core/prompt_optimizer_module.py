from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .kernel_protocol import KernelAPI, KernelModule
from .models import Task, AgentResult, TaskStatus

logger = logging.getLogger("prompt_optimizer")

@dataclass
class PromptOptimizerModule:
    name: str = "prompt_optimizer"
    _api: KernelAPI | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", f"[OPTIMIZER] {self.name} module loaded.")

    def on_unload(self) -> None:
        pass

    def before_task(self, task: Task, context: dict[str, Any]) -> None:
        """Inject relevant memories into the task description to optimize the prompt."""
        if not self._api:
            return

        # 1. Access HybridMemory via Orchestrator (self._api)
        # Note: self._api is the Orchestrator instance
        memory = self._api.get_context("session_memory")
        if not memory:
            return

        # 2. Retrieve recent relevant episodic memories
        session_id = task.session_id or "default"
        # We retrieve the last few successful results as examples
        recent_successes = memory.hybrid.get_command_history(session_id=session_id, limit=3)
        
        if recent_successes:
            examples_text = "\n[RELEVANT CONTEXT FROM MEMORY]:\n"
            for cmd in recent_successes:
                if cmd.get("success"):
                    examples_text += f"- Past Command: {cmd.get('command')}\n  Result Summary: {cmd.get('result', {}).get('summary', '')}\n"
            
            # 3. Augment task description
            # We don't overwrite the original object if we want to be surgical, 
            # but for the runner to see it, we can append to the context or description.
            if examples_text.strip():
                task.input.description += examples_text
                self._api.log("info", f"[OPTIMIZER] Augmented prompt with {len(recent_successes)} memories.")

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None:
        pass

    def finalize(self) -> dict[str, Any]:
        return {"status": "active"}
