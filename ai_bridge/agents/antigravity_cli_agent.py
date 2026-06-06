from __future__ import annotations

import os

from .base_agent import BaseAgent
from ai_bridge.core.external_ai_bridge import ExternalAIBridge
from ai_bridge.core.models import Task, TaskStatus
from ai_bridge.core.security import SecurityManager


class AntigravityCLIAgent(BaseAgent):
    def __init__(self, agent_id: str, security_manager: SecurityManager) -> None:
        super().__init__(agent_id, capabilities=["code", "review", "test", "docs", "research"])
        self.security = security_manager
        self.timeout_sec = self._resolve_timeout()

    def run(self, task: Task, memory_context: dict | None = None):
        prompt_parts = [task.input.description]
        if task.input.files:
            prompt_parts.append(f"FILES: {', '.join(task.input.files)}")
        if task.input.constraints:
            prompt_parts.append(f"CONSTRAINTS: {'; '.join(task.input.constraints)}")
        if task.input.acceptance_criteria:
            prompt_parts.append(f"ACCEPTANCE CRITERIA: {'; '.join(task.input.acceptance_criteria)}")

        prompt = "\n".join(prompt_parts)

        if not self.security.validate_shell_command("agy -p"):
            return self.result(task, "Security violation: Antigravity CLI command not allowed", TaskStatus.FAILED)

        self.active_tasks += 1
        try:
            bridge = ExternalAIBridge(None)
            bridge_result = bridge.run_antigravity_cli(task, prompt, timeout_sec=self.timeout_sec)

            if bridge_result.ok:
                return self.result(task, bridge_result.output, TaskStatus.DONE)

            self.last_error = bridge_result.error
            summary = f"Antigravity CLI unavailable (model={bridge_result.model}, attempts={bridge_result.attempts})"
            if bridge_result.error_type == "auth_fail":
                summary = "Antigravity CLI authentication required"
            elif "timeout" in bridge_result.error.lower():
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
        raw = os.getenv("ANTIGRAVITY_CLI_TIMEOUT_SEC", os.getenv("GEMINI_CLI_TIMEOUT_SEC", "120")).strip()
        try:
            timeout = int(raw)
        except ValueError:
            return 120
        return max(30, timeout)


GeminiCLIAgent = AntigravityCLIAgent
