from __future__ import annotations

import os
from typing import Any

from .base_agent import BaseAgent
from ai_bridge.core.models import AgentResult, Task, TaskStatus

try:  # preferred SDK
    from google import genai as google_genai  # type: ignore
except Exception:  # pragma: no cover
    google_genai = None  # type: ignore

try:  # legacy SDK fallback
    import google.generativeai as legacy_genai  # type: ignore
except Exception:  # pragma: no cover
    legacy_genai = None  # type: ignore


class GeminiAgent(BaseAgent):
    def __init__(self, agent_id: str, model_name: str = "gemini-2.5-flash") -> None:
        super().__init__(agent_id, capabilities=["code", "review", "test", "docs", "research"])
        self.model_name = model_name
        self._client: Any | None = None
        self._mode: str | None = None
        self._init_error: str | None = None
        self._configure_client()

    def _configure_client(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self._init_error = "GEMINI_API_KEY environment variable is required"
            return

        if google_genai is not None:
            try:
                self._client = google_genai.Client(api_key=api_key)
                self._mode = "google.genai"
                return
            except Exception as exc:  # pragma: no cover
                self._init_error = f"google.genai init failed: {exc}"

        if legacy_genai is not None:
            try:
                legacy_genai.configure(api_key=api_key)
                self._client = legacy_genai.GenerativeModel(self.model_name)
                self._mode = "google.generativeai"
                return
            except Exception as exc:  # pragma: no cover
                self._init_error = f"google.generativeai init failed: {exc}"

        if self._init_error is None:
            self._init_error = "No Gemini SDK installed (google.genai or google.generativeai)"

    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        self.active_tasks += 1
        try:
            if self._client is None:
                message = self._init_error or "Gemini client is not configured"
                self.last_error = message
                return self.result(task, "Gemini generation failed", TaskStatus.FAILED, errors=[message])

            prompt = task.input.description

            if self._mode == "google.genai":
                response = self._client.models.generate_content(model=self.model_name, contents=prompt)
                text = getattr(response, "text", None) or str(response)
                return self.result(task, text, TaskStatus.DONE)

            response = self._client.generate_content(prompt)
            text = getattr(response, "text", None) or str(response)
            return self.result(task, text, TaskStatus.DONE)
        except Exception as exc:
            self.last_error = str(exc)
            return self.result(task, "Gemini generation failed", TaskStatus.FAILED, errors=[str(exc)])
        finally:
            self.active_tasks = max(0, self.active_tasks - 1)
