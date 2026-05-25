import os
import subprocess

from .base_agent import BaseAgent
from ai_bridge.core.models import Task, TaskStatus
from ai_bridge.core.security import SecurityManager


class GeminiCLIAgent(BaseAgent):
    def __init__(self, agent_id: str, security_manager: SecurityManager) -> None:
        super().__init__(agent_id, capabilities=["code", "review", "test", "docs", "research"])
        self.security = security_manager
        self.timeout_sec = self._resolve_timeout()

    def run(self, task: Task):
        prompt = str(task.input.description)
        cmd = ["npx", "@google/gemini-cli", "--prompt", prompt, "--output-format", "text"]

        if not self.security.validate_shell_command(" ".join(cmd)):
            return self.result(task, "Security violation: CLI command not allowed", TaskStatus.FAILED)

        self.active_tasks += 1
        try:
            if self.host_bridge is not None:
                result = self.host_bridge.execute(cmd, timeout=self.timeout_sec, capture_output=True, text=True, check=False)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_sec)

            if result.returncode == 0:
                return self.result(task, result.stdout.strip(), TaskStatus.DONE)

            self.last_error = result.stderr
            return self.result(task, "CLI execution failed", TaskStatus.FAILED, errors=[result.stderr])
        except subprocess.TimeoutExpired as e:
            self.last_error = str(e)
            return self.result(task, "CLI execution timed out", TaskStatus.FAILED, errors=[str(e)])
        except Exception as e:
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
