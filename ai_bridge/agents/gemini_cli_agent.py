import subprocess
import os
from typing import Any
from .base_agent import BaseAgent
from ai_bridge.core.models import Task, AgentResult, TaskStatus
from ai_bridge.core.security import SecurityManager

class GeminiCLIAgent(BaseAgent):
    def __init__(self, agent_id: str, security_manager: SecurityManager) -> None:
        super().__init__(agent_id, capabilities=["code", "review", "test", "docs", "research"])
        self.security = security_manager

    def run(self, task: Task) -> AgentResult:
        # Construct command: npx @google/gemini-cli generate "<prompt>"
        # Sanitization: Basic shell escaping
        prompt = str(task.input.description).replace('"', '\\"')
        cmd = ["npx", "@google/gemini-cli", "generate", prompt]
        
        if not self.security.validate_shell_command(" ".join(cmd)):
            return self.result(task, "Security violation: CLI command not allowed", TaskStatus.FAILED)

        try:
            self.active_tasks += 1
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            self.active_tasks -= 1
            
            if result.returncode == 0:
                return self.result(task, result.stdout.strip(), TaskStatus.DONE)
            else:
                self.last_error = result.stderr
                return self.result(task, "CLI execution failed", TaskStatus.FAILED, errors=[result.stderr])
        except Exception as e:
            self.active_tasks -= 1
            self.last_error = str(e)
            return self.result(task, "CLI execution error", TaskStatus.FAILED, errors=[str(e)])
