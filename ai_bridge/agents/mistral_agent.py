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
            ["code", "fix", "test", "review", "docs", "research", "analysis", "summarization"],
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
        
        # Enriched prompt with context
        prompt_parts = [f"OBJECTIVE: {safe_context.get('description', '')}"]
        if task.input.files:
            prompt_parts.append(f"FILES: {', '.join(task.input.files)}")
        if task.input.constraints:
            prompt_parts.append(f"CONSTRAINTS: {'; '.join(task.input.constraints)}")
        if task.input.acceptance_criteria:
            prompt_parts.append(f"ACCEPTANCE CRITERIA: {'; '.join(task.input.acceptance_criteria)}")
        
        prompt_content = "\n".join(prompt_parts)
        
        # Prevent 'too many arguments' by truncating description
        if len(prompt_content) > 12000:
            prompt_content = prompt_content[:12000] + "... [TRUNCATED]"
            
        max_retries = 3
        last_exc = None
        
        for attempt in range(max_retries):
            try:
                response = httpx.post(
                    f"{self.endpoint}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
                        "messages": [{"role": "user", "content": prompt_content}],
                    },
                    timeout=45.0,
                )
                if response.status_code == 429:
                    # Exponential backoff for 429
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"Mistral 429 detected. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    import time
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return self.normalize_result(response.json(), task)
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    continue
                break
        
        self.last_error = str(last_exc)
        return self.result(task, "Mistral API error", TaskStatus.FAILED, 0.0, [str(last_exc)])

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
