from __future__ import annotations

import logging
from typing import Any

from .base_agent import BaseAgent
from ai_bridge.core.models import AgentResult, Task, TaskStatus

logger = logging.getLogger("local_llm_agent")


class LocalLLMAgent(BaseAgent):
    """
    LocalLLMAgent: uses a local LLM (Ollama) for task execution.
    """

    def __init__(self, agent_id: str, model_name: str = "qwen2.5:32b-instruct-q4_k_m") -> None:
        super().__init__(agent_id, capabilities=["code", "fix", "refactor", "test", "docs", "research", "review"])
        self.model_name = model_name

    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        self.active_tasks += 1
        try:
            # We need access to the bridge. We'll assume it's available via host_bridge or similar
            # In our case, the orchestrator sets host_bridge on agents.
            # However, the LocalLLMBridge is usually a separate component in Orchestrator.
            # For simplicity, we'll create a local bridge or use the one from context if possible.
            from ai_bridge.core.local_llm_bridge import LocalLLMBridge
            bridge = LocalLLMBridge(host_bridge=self.host_bridge)
            
            prompt = self._build_prompt(task)
            response = bridge.query(prompt, self.model_name)
            
            if response.startswith("Error:"):
                return self.result(task, response, TaskStatus.FAILED, errors=[response])
                
            return self.result(task, response, TaskStatus.DONE, confidence=0.85)
        except Exception as e:
            self.last_error = str(e)
            return self.result(task, "Local LLM execution error", TaskStatus.FAILED, errors=[str(e)])
        finally:
            self.active_tasks = max(0, self.active_tasks - 1)

    def _build_prompt(self, task: Task) -> str:
        prompt_parts = [
            f"SYSTEM: You are an AI assistant. Task Type: {task.type.value}.",
            f"OBJECTIVE: {task.input.description}"
        ]
        if task.input.files:
            prompt_parts.append(f"FILES: {', '.join(task.input.files)}")
        if task.input.constraints:
            prompt_parts.append(f"CONSTRAINTS: {'; '.join(task.input.constraints)}")
        if task.input.acceptance_criteria:
            prompt_parts.append(f"ACCEPTANCE CRITERIA: {'; '.join(task.input.acceptance_criteria)}")
        
        return "\n".join(prompt_parts)
