from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from openai import OpenAI

from .base_agent import BaseAgent
from ai_bridge.core.env_loader import load_env_file
from ai_bridge.core.openai_runtime_router import OpenAIRuntimeRouter
from ai_bridge.core.models import AgentHealth, AgentResult, AgentStatus, Task, TaskStatus

logger = logging.getLogger("codex_agent")
VISION_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".svg")


class CodexAgent(BaseAgent):
    """
    CodexAgent: specialized for high-quality code generation and refactoring.
    Can use OpenAI (GPT-4o) or Mistral (Codestral) based on available API keys.
    """

    def __init__(self, agent_id: str = "codexagent") -> None:
        super().__init__(agent_id, capabilities=["code", "fix", "refactor", "test"])
        load_env_file()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.mistral_key = os.getenv("MISTRAL_API_KEY")
        self._provider = "unknown"
        self._model = "unknown"
        self.openai_router = OpenAIRuntimeRouter()
        self._configure()

    def _configure(self) -> None:
        if self.openai_key:
            self._provider = "openai"
            self._model = os.getenv("CODEX_OPENAI_MODEL", "gpt-4o")
        elif self.mistral_key:
            self._provider = "mistral"
            self._model = os.getenv("CODEX_MISTRAL_MODEL", "codestral-latest")
        else:
            self._provider = "none"

    def health(self) -> AgentHealth:
        if self._provider == "none":
            return AgentHealth(self.agent_id, AgentStatus.FAILED, self.capabilities, last_error="no_api_keys_found")
        return AgentHealth(self.agent_id, AgentStatus.READY, self.capabilities)

    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        if self._provider == "none":
            return self.result(task, "No API key (OpenAI or Mistral) for Codex", TaskStatus.FAILED, errors=["OPENAI_API_KEY or MISTRAL_API_KEY missing"])

        self.active_tasks += 1
        try:
            prompt = self._build_prompt(task)
            
            if self._provider == "openai":
                return self._run_openai(task, prompt)
            else:
                return self._run_mistral(task, prompt)
        except Exception as e:
            self.last_error = str(e)
            return self.result(task, "Codex execution error", TaskStatus.FAILED, errors=[str(e)])
        finally:
            self.active_tasks = max(0, self.active_tasks - 1)

    def _build_prompt(self, task: Task) -> str:
        prompt_parts = [
            "SYSTEM: You are an elite software engineer (Codex Agent). Generate precise, idiomatic, and verified code.",
            f"OBJECTIVE: {task.input.description}"
        ]
        if task.input.files:
            prompt_parts.append(f"FILES: {', '.join(task.input.files)}")
            image_refs = [p for p in task.input.files if p.lower().endswith(VISION_EXTENSIONS)]
            if image_refs:
                prompt_parts.append(
                    "VISION MODE: Use referenced images as UI truth-source. "
                    "Extract layout, spacing rhythm, hierarchy, contrast, and component states."
                )
                prompt_parts.append(f"IMAGE_REFERENCES: {', '.join(image_refs)}")
                prompt_parts.append(
                    "UI OUTPUT REQUIREMENTS: Return production-ready frontend changes "
                    "(semantic HTML, accessible labels, responsive CSS, tokenized styles)."
                )
        if task.input.constraints:
            prompt_parts.append(f"CONSTRAINTS: {'; '.join(task.input.constraints)}")
        if task.input.acceptance_criteria:
            prompt_parts.append(f"ACCEPTANCE CRITERIA: {'; '.join(task.input.acceptance_criteria)}")
        
        return "\n".join(prompt_parts)

    def _run_openai(self, task: Task, prompt: str) -> AgentResult:
        client = OpenAI(api_key=self.openai_key)
        model = task.assigned_model or self._model
        if OpenAIRuntimeRouter.enabled():
            model = self.openai_router.select_model(task, prompt)
            task.assigned_model = model
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        total_tokens = int(getattr(usage, "total_tokens", 0) or 0) if usage else 0
        if total_tokens:
            self.openai_router.register_usage(task, total_tokens)
        result = self.result(task, content, TaskStatus.DONE, 0.9)
        result.provider = "openai"
        result.model_name = model
        return result

    def _run_mistral(self, task: Task, prompt: str) -> AgentResult:
        endpoint = "https://api.mistral.ai/v1/chat/completions"
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                endpoint,
                headers={"Authorization": f"Bearer {self.mistral_key}"},
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"] or ""
            return self.result(task, content, TaskStatus.DONE, 0.88)
