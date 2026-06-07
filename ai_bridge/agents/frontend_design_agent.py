from __future__ import annotations

from pydantic import BaseModel, Field
from ai_bridge.agents.base_agent import BaseAgent
from ai_bridge.core.models import AgentResult, Task, TaskStatus, AgentStatus

class UITokens(BaseModel):
    colors: dict[str, str] = Field(description="Tailwind color palette tokens")
    spacing: dict[str, str] = Field(description="Spacing scale tokens")
    typography: dict[str, str] = Field(description="Font size and weight tokens")
    border_radius: str = Field(description="Base border radius token")

class FrontendDesignAgent(BaseAgent):
    def __init__(self, agent_id: str = "frontend-design-1") -> None:
        super().__init__(agent_id, ["design", "code", "review"])

    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        self.orchestrator._broadcast_pod_state(self.agent_id, AgentStatus.BUSY, task.task_id)
        
        reasoning = self.orchestrator.get_module("reasoning")
        
        prompt = f"Design a minimalist UI system for a CRM admin console. Task: {task.input.description}"
        system_prompt = "You are a senior UI/UX designer. Output a JSON object with color, spacing, typography, and borderRadius tokens."
        
        tokens = reasoning.structured_call(prompt, UITokens, system_prompt=system_prompt)
        
        if not tokens:
            self.orchestrator._broadcast_pod_state(self.agent_id, AgentStatus.READY)
            return self.result(task, "Design generation failed", status=TaskStatus.FAILED, confidence=0.0)

        # Store tokens in memory for FrontendDevAgent to use
        self.orchestrator.session_memory.set("agent", self.agent_id, "ui_tokens", tokens.model_dump())
        
        summary = "Generated minimalist design tokens for CRM."
        self.orchestrator._broadcast_pod_state(self.agent_id, AgentStatus.READY)
        return self.result(task, summary, status=TaskStatus.DONE, confidence=0.95)
