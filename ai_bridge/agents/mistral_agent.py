from __future__ import annotations

import os
from typing import Any

import httpx

from .external_ai_agent import ExternalAIAgent
from ai_bridge.core.env_loader import load_env_file
from ai_bridge.core.models import AgentHealth, AgentResult, AgentStatus, Task, TaskStatus


class MistralAgent(ExternalAIAgent):
    provider = "mistral"

    def __init__(self, agent_id: str, security_manager: Any) -> None:
        super().__init__(
            agent_id,
            "https://api.mistral.ai/v1",
            ["analysis", "research", "docs", "summarization", "simple_code"],
            security=security_manager,
        )
        load_env_file()
        self.api_key = os.getenv("MISTRAL_API_KEY")

    def health(self) -> AgentHealth:
        if not self.api_key:
            return AgentHealth(self.agent_id, AgentStatus.FAILED, self.capabilities, last_error="auth_missing")
        return AgentHealth(self.agent_id, AgentStatus.READY, self.capabilities)

    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        if not self.api_key:
            return self.result(task, "Auth missing", TaskStatus.FAILED, 0.0, ["MISTRAL_API_KEY not set"])

        safe_context = self.redact_context(task)
        try:
            response = httpx.post(
                f"{self.endpoint}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
                    "messages": [{"role": "user", "content": safe_context["description"]}],
                },
                timeout=45.0,
            )
            response.raise_for_status()
            return self.normalize_result(response.json(), task)
        except Exception as exc:
            self.last_error = str(exc)
            return self.result(task, "Mistral API error", TaskStatus.FAILED, 0.0, [str(exc)])

    def redact_context(self, task: Task) -> dict:
        return self.security.safe_context_for_external_ai(
            {
                "description": task.input.description,
                "acceptance_criteria": task.input.acceptance_criteria,
            }
        )

    def normalize_result(self, response: dict, task: Task) -> AgentResult:
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            return self.result(task, "Empty response", TaskStatus.FAILED, 0.0, ["Model returned empty content"])
        return self.result(task, content, TaskStatus.DONE, 0.85, [])
