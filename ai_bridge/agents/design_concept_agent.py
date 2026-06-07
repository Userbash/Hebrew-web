from __future__ import annotations

from typing import Any

from ai_bridge.agents.base_agent import BaseAgent


class DesignConceptAgent(BaseAgent):
    def __init__(self):
        super().__init__("design_concept_agent", ["design_generation"])
        self._adapter_cache = None

    @property
    def manager(self):
        if self._adapter_cache is None and self.host_bridge is not None:
            module = self.host_bridge.get_module("easy_diffusion")
            if module:
                self._adapter_cache = module.manager
        return self._adapter_cache

    @staticmethod
    def _is_design_task(task: Any) -> bool:
        capability = str(getattr(task, "required_capability", "") or "").strip().lower()
        if capability == "design_generation":
            return True
        description = str(getattr(getattr(task, "input", None), "description", "") or "").lower()
        return any(token in description for token in ("design", "mockup", "image", "render", "illustration"))

    def _build_design_payload(self, task: Any, memory_context: dict[str, Any] | None = None) -> dict[str, Any]:
        memory = memory_context or {}
        spec = memory.get("design_spec") if isinstance(memory.get("design_spec"), dict) else {}
        return {
            "brief": spec.get("brief") or getattr(getattr(task, "input", None), "description", ""),
            "layout": spec.get("layout") or memory.get("layout") or "dashboard",
            "vibe": spec.get("vibe") or memory.get("vibe") or "modern",
            "primary_color": spec.get("primary_color") or memory.get("primary_color") or "",
            "components": spec.get("components") or memory.get("components") or [],
            "target_surface": spec.get("target_surface") or memory.get("target_surface") or "web",
            "output_name": memory.get("output_name") or spec.get("output_name") or "",
        }

    def run(self, task: Any, memory_context: dict[str, Any] | None = None) -> Any:
        from ai_bridge.core.models import AgentResult, TaskStatus

        if not self._is_design_task(task):
            return AgentResult(
                task.task_id,
                self.agent_id,
                TaskStatus.FAILED,
                {"status": "error", "message": "Task is not routed for design generation"},
                0.0,
                ["task_not_routed_for_design_generation"],
                [],
            )

        if not self.manager:
            result = {"status": "error", "message": "Image generation module not available"}
        else:
            payload = self._build_design_payload(task, memory_context=memory_context)
            overrides = dict(memory_context or {})
            try:
                result = self.manager.generate_design_image(payload, overrides=overrides)
            except Exception as exc:
                result = {"status": "error", "message": str(exc)}

        status = TaskStatus.DONE if result.get("status") == "success" else TaskStatus.FAILED
        confidence = 1.0 if status == TaskStatus.DONE else 0.0
        errors = [] if status == TaskStatus.DONE else [str(result.get("message") or "design_generation_failed")]
        return AgentResult(task.task_id, self.agent_id, status, result, confidence, errors, [])
