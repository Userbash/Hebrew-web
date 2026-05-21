import os
import httpx
from typing import Any
from .external_ai_agent import ExternalAIAgent
from ai_bridge.core.models import AgentResult, Task, TaskStatus, AgentStatus, AgentHealth

class DeepSeekAgent(ExternalAIAgent):
    provider = "deepseek"

    def __init__(self, agent_id: str, security_manager: Any) -> None:
        super().__init__(agent_id, "https://api.deepseek.com", 
                         ["analysis", "research", "docs", "summarization", "simple_code"], 
                         security=security_manager)
        self.api_key = os.getenv("DEEPSEEK_API_KEY")

    def health(self) -> AgentHealth:
        if not self.api_key:
            return AgentHealth(self.agent_id, AgentStatus.FAILED, self.capabilities, last_error="auth_missing")
        
        # Simple ping-like check
        return AgentHealth(self.agent_id, AgentStatus.READY, self.capabilities)

    async def execute(self, task: Task) -> AgentResult:
        if not self.api_key:
            return self.result(task, "Auth missing", TaskStatus.FAILED, 0.0, ["DEEPSEEK_API_KEY not set"])

        safe_context = self.redact_context(task)
        
        # OpenAI-compatible API call
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.endpoint}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": safe_context["description"]}],
                        "stream": False
                    },
                    timeout=45.0
                )
                response.raise_for_status()
                return self.normalize_result(response.json(), task)
            except Exception as e:
                return self.result(task, "DeepSeek API error", TaskStatus.FAILED, 0.0, [str(e)])

    def redact_context(self, task: Task) -> dict:
        return self.security.safe_context_for_external_ai({
            "description": task.input.description,
            "acceptance_criteria": task.input.acceptance_criteria
        })

    def normalize_result(self, response: dict, task: Task) -> AgentResult:
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            return self.result(task, "Empty response", TaskStatus.FAILED, 0.0, ["Model returned empty content"])
        
        # DeepSeek cannot finalize
        return self.result(task, content, TaskStatus.DONE, 0.85, [])
