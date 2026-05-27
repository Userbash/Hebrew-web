from __future__ import annotations

import os

from .base_agent import BaseAgent
from ai_bridge.core.external_ai_bridge import ExternalAIBridge
from ai_bridge.core.models import Task, TaskStatus
from ai_bridge.core.security import SecurityManager


class GeminiCLIAgent(BaseAgent):
    def __init__(self, agent_id: str, security_manager: SecurityManager) -> None:
        super().__init__(agent_id, capabilities=["code", "review", "test", "docs", "research"])
        self.security = security_manager
        self.timeout_sec = self._resolve_timeout()

    def run(self, task: Task, memory_context: dict | None = None):
        # Enriched prompt with context
        prompt_parts = [f"OBJECTIVE: {task.input.description}"]
        if task.input.files:
            prompt_parts.append(f"FILES: {', '.join(task.input.files)}")
        if task.input.constraints:
            prompt_parts.append(f"CONSTRAINTS: {'; '.join(task.input.constraints)}")
        if task.input.acceptance_criteria:
            prompt_parts.append(f"ACCEPTANCE CRITERIA: {'; '.join(task.input.acceptance_criteria)}")
        
        prompt = "\n".join(prompt_parts)
        
        # Validate command intent before executing external CLI.
        intent_cmd = "npx @google/gemini-cli --prompt"
        if not self.security.validate_shell_command(intent_cmd):
            return self.result(task, "Security violation: CLI command not allowed", TaskStatus.FAILED)

        self.active_tasks += 1
        try:
            bridge = ExternalAIBridge(self.host_bridge)
            bridge_result = bridge.run_gemini_cli(task, prompt, timeout_sec=self.timeout_sec)

            if bridge_result.ok:
                return self.result(task, bridge_result.output, TaskStatus.DONE)

            self.last_error = bridge_result.error
            summary = f"Gemini CLI unavailable (model={bridge_result.model}, attempts={bridge_result.attempts})"
            if "timeout" in bridge_result.error.lower():
                summary = "CLI execution timed out"
            return self.result(
                task,
                summary,
                TaskStatus.FAILED,
                errors=[bridge_result.error],
            )
        except Exception as e:  # pragma: no cover - guardrail
            self.last_error = str(e)
            return self.result(task, "CLI execution error", TaskStatus.FAILED, errors=[str(e)])
        finally:
            self.active_tasks = max(0, self.active_tasks - 1)

    @staticmethod
    def _resolve_timeout() -> int:
        raw = os.getenv("GEMINI_CLI_TIMEOUT_SEC", "120").strip()
        try:
            timeout = int(raw)
        except ValueError:
            return 120
        return max(30, timeout)
