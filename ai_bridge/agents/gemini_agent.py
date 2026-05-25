import os
import google.generativeai as genai
from typing import Any
from .base_agent import BaseAgent
from ai_bridge.core.models import Task, AgentResult, TaskStatus

class GeminiAgent(BaseAgent):
    def __init__(self, agent_id: str, model_name: str = "gemini-1.5-pro") -> None:
        super().__init__(agent_id, capabilities=["code", "review", "test", "docs", "research"])
        self.model_name = model_name
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required for GeminiAgent")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        try:
            self.active_tasks += 1
            response = self.model.generate_content(task.input.data)
            self.active_tasks -= 1
            return self.result(task, response.text, TaskStatus.DONE)
        except Exception as e:
            self.active_tasks -= 1
            self.last_error = str(e)
            return self.result(task, "Gemini generation failed", TaskStatus.FAILED, errors=[str(e)])
