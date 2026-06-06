from __future__ import annotations

import logging
from typing import Any

from .external_ai_bridge import ExternalAIBridge
from .kernel_protocol import KernelAPI
from .models import AgentResult, Task, TaskType

logger = logging.getLogger("prompt_optimizer")


class PromptOptimizerModule:
    name: str = "prompt_optimizer"
    _api: KernelAPI | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", f"[OPTIMIZER] {self.name} module loaded.")

    def on_unload(self) -> None:
        pass

    def _memory_history(self, task: Task) -> list[dict[str, Any]]:
        if not self._api:
            return []
        memory = self._api.get_context("session_memory")
        if not memory or not hasattr(memory, "hybrid"):
            return []
        session_id = task.session_id or "default"
        try:
            history = memory.hybrid.get_command_history(session_id=session_id, limit=3)
            return history if isinstance(history, list) else []
        except Exception:
            return []

    @staticmethod
    def _safe_offload_types() -> set[TaskType]:
        return {TaskType.PLAN, TaskType.DOCS, TaskType.RESEARCH, TaskType.REVIEW, TaskType.TEST}

    def _local_llm(self, task: Task, context: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not self._api:
            return None
        module_manager = self._api.get_context("module_manager")
        local_llm = module_manager.get_module("local_llm") if module_manager and hasattr(module_manager, "get_module") else None
        if not local_llm or not hasattr(local_llm, "build_offload_profile"):
            return None
        if task.type not in self._safe_offload_types():
            return None
        try:
            return local_llm.build_offload_profile(task, {**context, "memory_hits": history})
        except Exception as exc:
            self._api.log("warning", f"[OPTIMIZER] local_llm offload profile failed: {exc}")
            return None

    def _antigravity_rewrite(self, task: Task, instruction: str) -> str | None:
        if not self._api:
            return None
        host_bridge = self._api.get_context("host_bridge")
        bridge = ExternalAIBridge(host_bridge=host_bridge)
        prompt = (
            "Rewrite the instruction for an orchestrator. Return concise JSON or a structured instruction. "
            "Keep the original meaning, add concrete steps, preserve safety boundaries, and do not invent requirements.\\n\\n"
            f"Original instruction:\\n{instruction}"
        )
        try:
            result = bridge.run_antigravity_cli(task, prompt, timeout_sec=90)
            if result.ok and result.output.strip():
                return result.output.strip()
        except Exception as exc:
            self._api.log("warning", f"[OPTIMIZER] antigravity rewrite failed: {exc}")
        return None

    def _compose_instruction(self, task: Task, history: list[dict[str, Any]], offload: dict[str, Any] | None) -> str:
        base = task.input.description.strip()
        lines = [base]

        if history:
            compact_history = []
            for cmd in history:
                if not cmd.get("success"):
                    continue
                summary = str(cmd.get("result", {}).get("summary", "") or "").strip()
                if summary:
                    compact_history.append(f"- {cmd.get('command')}: {summary[:180]}")
            if compact_history:
                lines.append("Relevant prior successful context:")
                lines.extend(compact_history[:3])

        if offload:
            advisory_summary = str(offload.get("summary") or "").strip()
            next_steps = offload.get("next_steps") if isinstance(offload.get("next_steps"), list) else []
            if advisory_summary:
                lines.append(f"Local LLM summary: {advisory_summary[:400]}")
            if next_steps:
                lines.append("Suggested steps:")
                lines.extend(f"- {step}" for step in next_steps[:5])
            safe = offload.get("offload") if isinstance(offload.get("offload"), dict) else {}
            if isinstance(safe, dict):
                full_offload = safe.get("full_offload", [])
                partial_offload = safe.get("partial_offload", [])
                if full_offload or partial_offload:
                    lines.append(f"Offload policy: full={full_offload}; partial={partial_offload}")

        lines.append("Instruction for orchestrator:")
        lines.append("1. Preserve original user intent.")
        lines.append("2. Extract explicit requirements, constraints, and acceptance criteria.")
        lines.append("3. Separate safe analysis from risky mutations.")
        lines.append("4. Fan out independent work only when dependencies are explicit.")
        lines.append("5. Return a structured task plan with agent responsibilities.")
        return "\n".join(lines)

    def before_task(self, task: Task, context: dict[str, Any]) -> None:
        if not self._api:
            return

        history = self._memory_history(task)
        offload = self._local_llm(task, context, history) if history else self._local_llm(task, context, [])
        instruction = self._compose_instruction(task, history, offload)

        rewritten = None
        if offload and task.type in self._safe_offload_types():
            rewritten = self._antigravity_rewrite(task, instruction)

        final_instruction = rewritten or instruction
        task.input.description = final_instruction
        if not task.routing_hints:
            task.routing_hints = {}
        task.routing_hints["prompt_optimizer"] = {
            "history_items": len(history),
            "local_llm_used": bool(offload),
            "antigravity_used": bool(rewritten),
            "source": "prompt_optimizer",
        }
        self._api.log(
            "info",
            f"[OPTIMIZER] Prompt prepared: history={len(history)} local_llm={bool(offload)} antigravity={bool(rewritten)}",
        )

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None:
        pass

    def finalize(self) -> dict[str, Any]:
        return {"status": "active"}
