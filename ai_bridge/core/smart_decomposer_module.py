from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional

try:
    import ai_bridge.core.fix_imports  # noqa: F401
except ImportError:
    pass

import instructor
from openai import OpenAI
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
    _client: Any | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        # Initialize instructor client with OpenAI (or any compatible provider)
        # For local safety, we check for API key
        import os
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("MISTRAL_API_KEY")
        base_url = "https://api.mistral.ai/v1" if os.getenv("MISTRAL_API_KEY") else None
        
        if api_key:
            self._client = instructor.from_openai(OpenAI(api_key=api_key, base_url=base_url))
            self._api.log("info", f"[DECOMP] {self.name} loaded with instructor support.")
        else:
            self._api.log("warn", f"[DECOMP] {self.name} loaded without LLM client (missing keys). Falling back to legacy.")

    def on_unload(self) -> None:
        pass

    def decompose_task(self, root_task: Task) -> Optional[ExecutionPlan]:
        if not self._client or root_task.type != TaskType.PLAN:
            return None

        try:
            self._api.log("info", f"[DECOMP] Smartly decomposing task: {root_task.task_id}")
            
            # Request structured decomposition
            response: DecompositionResponse = self._client.chat.completions.create(
                model="mistral-large-latest", # Defaulting to mistral if available
                response_model=DecompositionResponse,
                messages=[
                    {"role": "system", "content": "You are an expert task decomposer. Break down the user request into technical atomic tasks."},
                    {"role": "user", "content": root_task.input.description}
                ]
            )

            atomic_tasks = []
            id_map = {} # Map LLM string ID to UUIDs

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
                
                # 4. Resolve dependencies (simple string matching for this demo)
                for dep in st.dependencies:
                    if dep in id_map:
                        task.dependencies.append(id_map[dep])
                
                atomic_tasks.append(task)

            self._api.log("info", f"[DECOMP] Generated {len(atomic_tasks)} atomic tasks via LLM.")
            return ExecutionPlan(root_task_id=root_task.task_id, atomic_tasks=atomic_tasks)

        except Exception as e:
            logger.exception("Smart decomposition failed: %s", e)
            return None

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        pass

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        pass

    def finalize(self) -> dict[str, Any]:
        return {"status": "active" if self._client else "fallback_only"}
