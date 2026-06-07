from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional

try:
    import ai_bridge.core.fix_imports  # noqa: F401
except ImportError:
    pass

from pydantic import BaseModel, Field

from .kernel_protocol import KernelAPI, KernelModule
from .models import Task, TaskType, Priority, ExecutionPlan, TaskInput, TaskContext

logger = logging.getLogger("smart_decomposer")

class SubTask(BaseModel):
    title: str
    description: str
    task_type: str = Field(description="One of: plan, code, review, test, docs, fix, research")
    priority: str = Field(default="normal")
    dependencies: List[str] = Field(default_factory=list, description="IDs of tasks this task depends on (e.g. task_0, task_1)")

class DecompositionResponse(BaseModel):
    plan_summary: str
    tasks: List[SubTask]

@dataclass
class SmartDecomposerModule:
    name: str = "smart_decomposer"
    _api: KernelAPI | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", f"[DECOMP] {self.name} loaded.")

    def on_unload(self) -> None:
        pass

    def decompose_task(self, root_task: Task) -> Optional[ExecutionPlan]:
        if not self._api or root_task.type != TaskType.PLAN:
            return None

        reasoning = self._api.get_module("reasoning")
        if not reasoning or not getattr(reasoning, "_client", None):
            return None

        try:
            self._api.log("info", f"[DECOMP] Smartly decomposing task: {root_task.task_id}")
            
            prompt = f"Break down the following user request into technical atomic tasks: {root_task.input.description}"
            system_prompt = "You are an expert task decomposer and system architect. Create a detailed execution plan with atomic sub-tasks."
            
            # Request structured decomposition using a thinking model if available
            response: DecompositionResponse = reasoning.structured_call(
                prompt, 
                DecompositionResponse, 
                system_prompt=system_prompt,
                model="gemini-3.5-flash"
            )
            
            if not response:
                return None

            atomic_tasks = []
            id_map = {}  # Map LLM string ID to UUIDs
            raw_dependencies: list[tuple[Task, list[str]]] = []

            for i, st in enumerate(response.tasks):
                # 1. Map type
                try:
                    t_type = TaskType(st.task_type.lower())
                except ValueError:
                    t_type = TaskType.CODE
                
                # 2. Create Task
                task = Task(
                    type=t_type,
                    input=TaskInput(description=st.description, acceptance_criteria=[f"{st.title} completed"]),
                    context=root_task.context,
                    priority=Priority(st.priority.lower()) if st.priority.lower() in ["low", "normal", "high", "critical"] else Priority.NORMAL,
                    parent_task_id=root_task.task_id
                )
                
                # 3. Store ID for dependency resolution
                id_map[f"task_{i}"] = task.task_id
                id_map[st.title.lower().replace(" ", "_")] = task.task_id
                
                # Resolve dependencies in a second pass so forward references also work.
                raw_dependencies.append((task, list(st.dependencies)))
                atomic_tasks.append(task)

            # Second pass dependency resolution.
            for task, deps in raw_dependencies:
                for dep in deps:
                    dep_key = dep.strip()
                    dep_id = id_map.get(dep_key)
                    if dep_id and dep_id != task.task_id and dep_id not in task.dependencies:
                        task.dependencies.append(dep_id)

            self._api.log("info", f"[DECOMP] Generated {len(atomic_tasks)} atomic tasks via AI Reasoning.")
            return ExecutionPlan(root_task_id=root_task.task_id, atomic_tasks=atomic_tasks)

        except Exception as e:
            logger.exception("Smart decomposition failed: %s", e)
            return None

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        pass

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        pass

    def finalize(self) -> dict[str, Any]:
        reasoning = self._api.get_module("reasoning") if self._api else None
        ready = bool(reasoning and getattr(reasoning, "_client", None))
        return {"status": "active" if ready else "fallback_only"}
