from __future__ import annotations

from ai_bridge.agents.codex_agent import CodexAgent
from ai_bridge.core.models import AgentResult, Task

VISION_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".svg")


class FrontendDevAgent(CodexAgent):
    def __init__(self, agent_id: str = "frontend-dev-1") -> None:
        super().__init__(agent_id)
        self.capabilities = ["code", "fix", "test", "docs", "review"]

    def run(self, task: Task, memory_context: dict | None = None) -> AgentResult:
        scoped_task = Task(
            type=task.type,
            input=task.input,
            context=task.context,
            priority=task.priority,
            task_id=task.task_id,
            parent_task_id=task.parent_task_id,
            dependencies=task.dependencies,
            retry_count=task.retry_count,
            required_capability=task.required_capability,
            assigned_model=task.assigned_model,
            memory_scope=task.memory_scope,
            memory_ttl_sec=task.memory_ttl_sec,
            memory_keys=task.memory_keys,
            cache_policy=task.cache_policy,
            session_id=task.session_id,
        )
        scoped_task.input.constraints = list(scoped_task.input.constraints) + [
            "Target: frontend-react",
            "Preserve existing design system and routing",
            "Ensure desktop/mobile responsiveness",
            "Use AI vision reasoning for UI image refs when provided",
            "Generate reusable components and design tokens",
            "Prefer semantic HTML and WCAG-friendly contrast/focus states",
        ]
        image_refs = [f for f in scoped_task.input.files if f.lower().endswith(VISION_EXTENSIONS)]
        if image_refs:
            scoped_task.input.acceptance_criteria = list(scoped_task.input.acceptance_criteria) + [
                "UI structure matches image references",
                "Spacing/typography hierarchy preserved from references",
                "Responsive behavior retained across breakpoints",
            ]
        return super().run(scoped_task, memory_context=memory_context)
