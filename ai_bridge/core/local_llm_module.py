from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests

from .kernel_protocol import KernelAPI, KernelModule

logger = logging.getLogger("local_llm_module")

HIGH_RISK_KEYWORDS = (
    "security",
    "auth",
    "rbac",
    "payment",
    "secret",
    "production",
    "migration",
    "destructive",
)
LOCAL_LLM_TASK_KEYWORDS = {
    "repo_ops": ("repo", "repository", "worktree", "branch", "status", "diff", "clone", "checkout"),
    "docs_workflow": ("docs", "documentation", "summary", "explain", "commit message", "commit log"),
    "verification": ("test", "tests", "ci", "verification", "checklist", "health", "workflow"),
    "planning": ("plan", "plan:", "break down", "decompose", "roadmap"),
    "analysis": ("research", "review", "analysis", "compare", "investigate"),
}


class LocalLLMModule(KernelModule):
    def __init__(
        self,
        endpoint: str | None = None,
        model_name: str | None = None,
        timeout_sec: float | None = None,
    ) -> None:
        self.name = "local_llm"
        self.endpoint = (endpoint or os.getenv("AI_BRIDGE_LOCAL_LLM_ENDPOINT") or "http://127.0.0.1:11434").rstrip("/")
        self.model_name = model_name or os.getenv("AI_BRIDGE_LOCAL_LLM_MODEL") or "qwen2.5:32b-instruct-q4_k_m"
        raw_timeout = os.getenv("AI_BRIDGE_LOCAL_LLM_HEALTH_TIMEOUT_SEC")
        if timeout_sec is not None:
            self.timeout_sec = max(0.2, timeout_sec)
        elif raw_timeout:
            try:
                self.timeout_sec = max(0.2, float(raw_timeout))
            except ValueError:
                self.timeout_sec = 1.0
        else:
            self.timeout_sec = 1.0
        self.last_probe: dict[str, Any] = {}
        self.last_advisory: dict[str, Any] = {}

    @staticmethod
    def _model_matches(expected: str, candidate: str) -> bool:
        expected_base = expected.split(":", 1)[0]
        candidate_base = candidate.split(":", 1)[0]
        return candidate == expected or candidate_base == expected_base

    @staticmethod
    def _task_text(task: Any, context: dict[str, Any] | None = None) -> str:
        pieces: list[str] = []
        if context:
            for key in ("description", "objective", "message", "prompt", "summary"):
                value = context.get(key)
                if isinstance(value, str) and value.strip():
                    pieces.append(value.strip())
        description = str(getattr(getattr(task, "input", None), "description", "") or "").strip()
        if description:
            pieces.append(description)
        task_type = str(getattr(getattr(task, "type", None), "value", getattr(task, "type", ""))).strip()
        if task_type:
            pieces.append(task_type)
        files = getattr(getattr(task, "input", None), "files", []) or []
        if isinstance(files, list):
            pieces.extend(str(item) for item in files if str(item).strip())
        constraints = getattr(getattr(task, "input", None), "constraints", []) or []
        if isinstance(constraints, list):
            pieces.extend(str(item) for item in constraints if str(item).strip())
        return " ".join(pieces).lower()

    @staticmethod
    def _task_family(task_text: str) -> str:
        for family, keywords in LOCAL_LLM_TASK_KEYWORDS.items():
            if any(keyword in task_text for keyword in keywords):
                return family
        return "general"

    @staticmethod
    def _high_risk(task_text: str) -> bool:
        return any(keyword in task_text for keyword in HIGH_RISK_KEYWORDS)

    @staticmethod
    def _recommended_actions(task_family: str) -> list[str]:
        mapping = {
            "repo_ops": [
                "summarize the worktree and recent repository changes",
                "prepare a concise handoff for the orchestrator",
                "highlight immediate repo actions without mutating state",
            ],
            "docs_workflow": [
                "draft the documentation or commit text",
                "compress the change into a readable summary",
                "surface the outcome for the reviewer and orchestrator",
            ],
            "verification": [
                "prepare a test plan or checklist",
                "summarize verification steps for the core",
                "highlight likely failure points before execution",
            ],
            "planning": [
                "break the task into smaller steps",
                "produce a lightweight execution outline",
                "identify which parts remain in the core",
            ],
            "analysis": [
                "summarize the options and tradeoffs",
                "prepare a comparison of likely approaches",
                "extract the useful context for the next agent",
            ],
        }
        return mapping.get(task_family, [
            "summarize the task",
            "compress context for the core",
        ])

    @staticmethod
    def _core_retained_actions() -> list[str]:
        return [
            "security enforcement",
            "provider routing",
            "scheduler decisions",
            "budget controls",
            "mutating execution",
            "failover and retries",
        ]

    def _probe(self) -> dict[str, Any]:
        response = requests.get(f"{self.endpoint}/api/tags", timeout=self.timeout_sec)
        response.raise_for_status()
        payload = response.json() if response.content else {}
        models = payload.get("models", []) if isinstance(payload, dict) else []
        available_models: list[str] = []
        if isinstance(models, list):
            for item in models:
                if isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str) and name.strip():
                        available_models.append(name.strip())
        model_present = any(self._model_matches(self.model_name, candidate) for candidate in available_models)
        return {
            "ok": True,
            "status_code": response.status_code,
            "available_models": available_models,
            "model_present": model_present,
            "error": None,
        }

    def query(self, prompt: str, model_name: str | None = None) -> str:
        model = model_name or self.model_name
        response = requests.post(
            f"{self.endpoint}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=max(2.0, self.timeout_sec * 10),
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        if isinstance(payload, dict):
            text = payload.get("response")
            if isinstance(text, str):
                return text.strip()
        return ""

    def _advisory_base(self, task: Any, context: dict[str, Any] | None = None) -> dict[str, Any]:
        probe = self.check_health()
        ready = bool(probe.get("ok")) and bool(probe.get("model_present"))
        task_text = self._task_text(task, context)
        task_family = self._task_family(task_text)
        task_type = str(getattr(getattr(task, "type", None), "value", getattr(task, "type", ""))).lower() or None
        complexity = str(getattr(getattr(task, "complexity", None), "value", getattr(task, "complexity", "")) or "").lower() or None
        priority = str(getattr(getattr(task, "priority", None), "value", getattr(task, "priority", "")) or "").lower() or None
        high_risk = self._high_risk(task_text) or priority == "critical"
        should_delegate = ready and not high_risk and task_family in {"docs_workflow", "verification", "planning", "analysis"}
        preferred_model = self.model_name if ready else None
        return {
            "enabled": ready,
            "ready": ready,
            "status": probe.get("status", "unknown") if isinstance(probe, dict) else "unknown",
            "endpoint": self.endpoint,
            "model_name": self.model_name,
            "task_family": task_family,
            "task_type": task_type,
            "priority": priority,
            "complexity": complexity,
            "high_risk": high_risk,
            "should_delegate": should_delegate,
            "recommended_owner": "local_llm" if should_delegate else "core",
            "recommended_model": preferred_model,
            "source_context": {
                "files": list(getattr(getattr(task, "input", None), "files", []) or []),
                "constraints": list(getattr(getattr(task, "input", None), "constraints", []) or []),
            },
            "actions": self._recommended_actions(task_family),
            "core_retained_actions": self._core_retained_actions(),
            "summary": None,
            "task_text": task_text,
        }

    def _heuristic_decomposition_draft(self, task: Any, context: dict[str, Any] | None = None) -> dict[str, Any]:
        task_text = self._task_text(task, context)
        task_family = self._task_family(task_text)
        plan_layers = [
            {
                "name": "intake",
                "objective": "Normalize the request and extract constraints",
                "capability": "plan",
                "tasks": ["summarize the request", "list explicit constraints", "capture acceptance criteria"],
                "sub_agents": ["planner"],
            },
            {
                "name": "analysis",
                "objective": "Identify implementation surfaces and risks",
                "capability": "research",
                "tasks": ["identify affected modules", "list integration points", "flag risk areas"],
                "sub_agents": ["research", "review"],
            },
            {
                "name": "implementation",
                "objective": "Create implementation chunks for the core agents",
                "capability": "code",
                "tasks": ["backend changes", "frontend changes", "data changes"],
                "sub_agents": ["backend", "frontend", "database"],
            },
            {
                "name": "verification",
                "objective": "Prepare test and validation work",
                "capability": "test",
                "tasks": ["unit tests", "integration tests", "verification checklist"],
                "sub_agents": ["tester", "review"],
            },
            {
                "name": "documentation",
                "objective": "Prepare the human-readable handoff",
                "capability": "docs",
                "tasks": ["update README", "write PR summary", "write commit summary"],
                "sub_agents": ["docs"],
            },
        ]
        if task_family == "repo_ops":
            plan_layers.insert(1, {
                "name": "repo_scan",
                "objective": "Inspect repository state and worktree changes",
                "capability": "docs",
                "tasks": ["repo status", "worktree diff", "changed files summary"],
                "sub_agents": ["sourcecraft"],
            })
        if task_family == "analysis":
            plan_layers[1]["tasks"] = ["compare approaches", "summarize tradeoffs", "identify risks"]
        return {
            "status": "heuristic",
            "task_family": task_family,
            "layers": plan_layers,
            "agent_map": {
                "planner": ["intake"],
                "research": ["analysis"],
                "backend": ["implementation"],
                "frontend": ["implementation"],
                "database": ["implementation"],
                "tester": ["verification"],
                "docs": ["documentation"],
                "sourcecraft": ["repo_scan"],
            },
            "sub_agents": ["planner", "research", "backend", "frontend", "database", "tester", "docs"],
        }

    def build_decomposition_draft(self, task: Any, context: dict[str, Any] | None = None) -> dict[str, Any]:
        advisory = self._advisory_base(task, context)
        if not advisory.get("ready"):
            advisory["decomposition"] = self._heuristic_decomposition_draft(task, context)
            return advisory

        task_text = advisory.get("task_text") or self._task_text(task, context)
        prompt = (
            "Return JSON only. Build a layered decomposition draft for an orchestrator. "
            "Use keys summary, context_digest, next_steps, model_hint, layers, agent_map, sub_agents, routing_hints, and verification. "
            "Each layer must have name, objective, capability, tasks, sub_agents, and dependencies. "
            "Keep it concise and practical. Task: "
            f"{task_text}"
        )
        parsed: dict[str, Any] | None = None
        try:
            response = self.query(prompt, self.model_name)
            if response:
                try:
                    raw = json.loads(response)
                    if isinstance(raw, dict):
                        parsed = raw
                except json.JSONDecodeError:
                    parsed = None
        except Exception as exc:
            advisory["decomposition_error"] = str(exc)

        if not parsed:
            parsed = self._heuristic_decomposition_draft(task, context)
            parsed["status"] = "heuristic"
        else:
            parsed.setdefault("status", "model")
            parsed.setdefault("task_family", advisory["task_family"])
            parsed.setdefault("sub_agents", [])
            parsed.setdefault("agent_map", {})
            parsed.setdefault("layers", [])

        advisory.update({
            "summary": parsed.get("summary") if isinstance(parsed.get("summary"), str) else advisory.get("summary"),
            "context_digest": parsed.get("context_digest") if isinstance(parsed.get("context_digest"), str) else None,
            "next_steps": parsed.get("next_steps") if isinstance(parsed.get("next_steps"), list) else advisory.get("actions", []),
            "model_hint": parsed.get("model_hint") if isinstance(parsed.get("model_hint"), str) else advisory.get("recommended_model"),
        })
        advisory["decomposition"] = parsed
        return advisory

    def build_advisory(self, task: Any, context: dict[str, Any] | None = None) -> dict[str, Any]:
        probe = self.check_health()
        ready = bool(probe.get("ok")) and bool(probe.get("model_present"))
        task_text = self._task_text(task, context)
        task_family = self._task_family(task_text)
        task_type = str(getattr(getattr(task, "type", None), "value", getattr(task, "type", ""))).lower() or None
        complexity = str(getattr(getattr(task, "complexity", None), "value", getattr(task, "complexity", "")) or "").lower() or None
        priority = str(getattr(getattr(task, "priority", None), "value", getattr(task, "priority", "")) or "").lower() or None
        high_risk = self._high_risk(task_text) or priority == "critical"
        should_delegate = ready and not high_risk and task_family in {"docs_workflow", "verification", "planning", "analysis"}
        preferred_model = self.model_name if ready else None
        advisory: dict[str, Any] = {
            "enabled": ready,
            "ready": ready,
            "status": probe.get("status", "unknown") if isinstance(probe, dict) else "unknown",
            "endpoint": self.endpoint,
            "model_name": self.model_name,
            "task_family": task_family,
            "task_type": task_type,
            "priority": priority,
            "complexity": complexity,
            "high_risk": high_risk,
            "should_delegate": should_delegate,
            "recommended_owner": "local_llm" if should_delegate else "core",
            "recommended_model": preferred_model,
            "source_context": {
                "files": list(getattr(getattr(task, "input", None), "files", []) or []),
                "constraints": list(getattr(getattr(task, "input", None), "constraints", []) or []),
            },
            "actions": self._recommended_actions(task_family),
            "core_retained_actions": self._core_retained_actions(),
            "summary": None,
        }

        if should_delegate:
            prompt = (
                "You are assisting an orchestrator. Return one short JSON object with keys summary, "
                "context_digest, next_steps, and model_hint. Keep it concise. Task: "
                f"{task_text}"
            )
            try:
                response = self.query(prompt, self.model_name)
                if response:
                    try:
                        parsed = json.loads(response)
                        if isinstance(parsed, dict):
                            advisory.update({
                                "summary": parsed.get("summary") if isinstance(parsed.get("summary"), str) else advisory.get("summary"),
                                "context_digest": parsed.get("context_digest") if isinstance(parsed.get("context_digest"), str) else None,
                                "next_steps": parsed.get("next_steps") if isinstance(parsed.get("next_steps"), list) else advisory["actions"],
                                "model_hint": parsed.get("model_hint") if isinstance(parsed.get("model_hint"), str) else preferred_model,
                            })
                    except json.JSONDecodeError:
                        advisory["summary"] = response[:240]
            except Exception as exc:
                advisory["summary"] = f"local_llm_unavailable: {exc}"

        self.last_advisory = advisory
        return advisory

    def on_load(self, api: KernelAPI) -> None:
        api.log("info", f"[LOCAL_LLM] Probing Ollama at {self.endpoint} for model {self.model_name}...")
        self.last_probe = self.check_health()
        if self.last_probe.get("ok") and self.last_probe.get("model_present"):
            api.log("info", f"[LOCAL_LLM] Local model {self.model_name} is reachable and ready.")
        elif self.last_probe.get("ok"):
            api.log("warning", f"[LOCAL_LLM] Ollama is reachable, but model {self.model_name} is not loaded yet.")
        else:
            api.log("error", f"[LOCAL_LLM] Local model endpoint is unreachable: {self.last_probe.get('error', 'unknown error')}")

    def on_unload(self) -> None:
        self.last_probe = {}
        self.last_advisory = {}

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        advisory = self.build_decomposition_draft(task, context)
        context["local_llm"] = advisory
        if advisory.get("should_delegate"):
            context["local_llm"]["automation"] = {
                "owner": "local_llm",
                "task_family": advisory.get("task_family"),
                "actions": advisory.get("actions", []),
                "core_retained_actions": advisory.get("core_retained_actions", []),
            }

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        local_llm = context.get("local_llm")
        if not isinstance(local_llm, dict):
            return
        output = getattr(result, "output", {})
        summary = ""
        if isinstance(output, dict):
            summary = str(output.get("summary", "") or "")
        local_llm["last_result"] = {
            "task_id": getattr(task, "task_id", None),
            "status": getattr(getattr(result, "status", None), "value", getattr(result, "status", None)),
            "summary": summary,
        }

    def check_health(self) -> dict[str, Any]:
        try:
            self.last_probe = self._probe()
        except Exception as exc:
            self.last_probe = {
                "ok": False,
                "status_code": None,
                "available_models": [],
                "model_present": False,
                "error": str(exc),
            }
        return self.last_probe

    def finalize(self) -> dict[str, Any]:
        probe = self.last_probe or self.check_health()
        ok = bool(probe.get("ok"))
        model_present = bool(probe.get("model_present"))
        if ok and model_present:
            status = "ready"
        elif ok:
            status = "degraded"
        else:
            status = "error"
        return {
            "status": status,
            "endpoint": self.endpoint,
            "model": self.model_name,
            "health_timeout_sec": self.timeout_sec,
            "service_reachable": ok,
            "model_present": model_present,
            "available_models": probe.get("available_models", []),
            "last_error": probe.get("error"),
            "advisory_examples": {
                "docs_workflow": self._recommended_actions("docs_workflow"),
                "verification": self._recommended_actions("verification"),
                "planning": self._recommended_actions("planning"),
                "analysis": self._recommended_actions("analysis"),
            },
            "last_advisory": self.last_advisory,
        }
