from __future__ import annotations

import asyncio
import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from .kernel_protocol import KernelAPI, KernelModule
from .task_submission_api import create_standard_task, normalize_user_payload

logger = logging.getLogger("api_bridge_module")


class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str
    source: Optional[str] = None
    provider: Optional[str] = None


class RegistrationRequest(BaseModel):
    provider_id: str
    callback_url: Optional[str] = None
    session_id: Optional[str] = None


class SourceCraftDelegateRequest(BaseModel):
    description: str
    task_type: str = "code"
    priority: str = "normal"
    repo_path: str = "."
    branch: str = "main"
    files: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    required_capability: str | None = None


@dataclass
class APIBridgeModule:
    name: str = "api_bridge"
    host: str = "0.0.0.0"
    port: int = 8000
    _api: KernelAPI | None = None
    _server_thread: threading.Thread | None = None
    _stop_event: asyncio.Event = field(default_factory=asyncio.Event)

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        enabled = os.getenv("AI_BRIDGE_API_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}
        self.host = os.getenv("AI_BRIDGE_API_HOST", self.host)
        try:
            self.port = int(os.getenv("AI_BRIDGE_API_PORT", str(self.port)))
        except ValueError:
            self.port = 8000

        self._api.log("info", f"[API] {self.name} module loading...")
        if not enabled:
            self._api.log("info", "[API] api_bridge disabled by AI_BRIDGE_API_ENABLED")
            return

        # We run the FastAPI server in a separate thread to not block the Orchestrator
        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()
        self._api.log("info", f"[API] {self.name} server started on {self.host}:{self.port}")

    def _sourcecraft_module(self):
        if not self._api:
            return None
        try:
            return self._api.get_module("sourcecraft")
        except Exception:
            return None

    def _sourcecraft_snapshot(self) -> dict[str, Any]:
        module = self._sourcecraft_module()
        if module and hasattr(module, "finalize"):
            return module.finalize()
        return {"status": "inactive", "role": {}, "use_cases": [], "delegation_matrix": []}

    def _sourcecraft_matrix(self) -> list[dict[str, Any]]:
        snapshot = self._sourcecraft_snapshot()
        matrix = snapshot.get("delegation_matrix") or []
        return matrix if isinstance(matrix, list) else []

    def _health_full_snapshot(self) -> dict[str, Any]:
        if not self._api:
            return {"status": "error", "message": "Kernel API not available"}

        healthcheck = self._api.get_context("healthcheck")
        registry = self._api.get_context("registry")
        module_manager = self._api.get_context("module_manager")

        provider_health: list[dict[str, Any]] = []
        agent_health: list[dict[str, Any]] = []
        summary: dict[str, Any] = {
            "provider_count": 0,
            "agent_count": 0,
            "ready_agents": 0,
            "problem_agents": 0,
            "problem_providers": 0,
        }

        if healthcheck:
            try:
                providers = healthcheck.check_providers()
                provider_health = [item.as_dict() for item in providers.values()]
            except Exception as exc:
                provider_health = [{"provider": "unknown", "status": "error", "error": str(exc)}]
            try:
                agents = healthcheck.check_all()
                agent_health = [item.as_dict() for item in agents]
            except Exception as exc:
                agent_health = [{"agent_id": "unknown", "status": "error", "last_error": str(exc)}]

        if provider_health:
            summary["provider_count"] = len(provider_health)
            summary["problem_providers"] = sum(1 for item in provider_health if item.get("status") not in {"healthy", "degraded"})
        if agent_health:
            summary["agent_count"] = len(agent_health)
            summary["ready_agents"] = sum(1 for item in agent_health if item.get("status") == "ready")
            summary["problem_agents"] = sum(1 for item in agent_health if item.get("status") != "ready")

        module_state = module_manager.finalize() if module_manager and hasattr(module_manager, "finalize") else {}
        sourcecraft = self._sourcecraft_snapshot()
        overall_ok = bool(provider_health) and bool(agent_health) and summary["problem_agents"] == 0 and summary["problem_providers"] == 0

        return {
            "status": "ok" if overall_ok else "degraded",
            "overall_ok": overall_ok,
            "summary": summary,
            "providers": provider_health,
            "agents": agent_health,
            "modules": module_state,
            "sourcecraft": sourcecraft,
            "registry_size": len(registry.list_agents()) if registry and hasattr(registry, "list_agents") else 0,
        }

    def _build_sourcecraft_task(self, request: SourceCraftDelegateRequest):
        from .models import Priority, Task, TaskContext, TaskInput, TaskType

        task_type = request.task_type.strip().lower()
        try:
            task_enum = TaskType(task_type)
        except Exception:
            task_enum = TaskType.CODE

        priority_raw = request.priority.strip().lower()
        priority_map = {"low": Priority.LOW, "normal": Priority.NORMAL, "high": Priority.HIGH, "critical": Priority.CRITICAL}
        priority = priority_map.get(priority_raw, Priority.NORMAL)
        task = Task(
            task_enum,
            TaskInput(request.description, files=request.files, constraints=request.constraints, acceptance_criteria=request.acceptance_criteria),
            TaskContext("sourcecraft", request.repo_path, request.branch),
            priority=priority,
        )
        task.required_capability = request.required_capability or "sourcecraft"
        return task

    def _chat_trace_payload(self, request: ChatRequest, *, source_label: str, provider_label: str) -> dict[str, Any]:
        if not self._api:
            return {"status": "error", "message": "Kernel API not available"}

        raw_payload = {
            "user_id": request.user_id,
            "message": request.message,
            "session_id": request.session_id,
            "source": source_label,
            "provider": provider_label,
        }
        normalized = normalize_user_payload(raw_payload)
        task = create_standard_task(normalized)

        control = self._api.get_module("orchestrator_control") if hasattr(self._api, "get_module") else None
        control_before = control.task_status(task.task_id) if control and hasattr(control, "task_status") else None
        result = self._api.submit_user_task(raw_payload, source=source_label)  # type: ignore[arg-type]
        result_task_id = task.task_id
        if isinstance(result, dict):
            submitted_task_id = result.get("task_id")
            if isinstance(submitted_task_id, str) and submitted_task_id.strip():
                result_task_id = submitted_task_id.strip()
        control_after = control.task_status(result_task_id) if control and hasattr(control, "task_status") else None
        if control_after is None and control and hasattr(control, "finalize"):
            snapshot = control.finalize()
            if isinstance(snapshot, dict):
                tasks = snapshot.get("tasks", {})
                if isinstance(tasks, dict):
                    control_after = tasks.get(result_task_id)

        live_trace = None
        if hasattr(self._api, "live_trace_rows") and getattr(self._api, "live_trace_rows", None):
            rows = list(getattr(self._api, "live_trace_rows"))
            live_trace = next((row for row in reversed(rows) if row.get("task_id") == result_task_id), rows[-1])

        scheduler_trace = None
        if hasattr(self._api, "scheduler") and getattr(self._api, "scheduler", None):
            decisions = list(getattr(self._api.scheduler, "decisions", []))
            if decisions:
                last = next((item for item in reversed(decisions) if getattr(item, "task_id", None) == result_task_id), decisions[-1])
                scheduler_trace = last.as_dict() if hasattr(last, "as_dict") else last

        return {
            "status": "completed",
            "source": source_label,
            "provider": provider_label,
            "input": raw_payload,
            "normalized": normalized,
            "task": {
                "task_id": result_task_id,
                "type": task.type.value,
                "priority": task.priority.value,
                "required_capability": task.required_capability,
                "repo_path": task.context.repo_path,
                "branch": task.context.branch,
            },
            "control": {
                "before": control_before,
                "after": control_after,
            },
            "route": live_trace,
            "schedule": scheduler_trace,
            "result": result,
        }

    def _sourcecraft_delegate(self, request: SourceCraftDelegateRequest) -> dict[str, Any]:
        if not self._api:
            return {"status": "error", "message": "Kernel API not available"}
        task = self._build_sourcecraft_task(request)
        router = self._api.get_context("router")
        scheduler = self._api.get_context("scheduler")
        sourcecraft_module = self._sourcecraft_module()
        delegation = None
        if sourcecraft_module and hasattr(sourcecraft_module, "build_delegation_profile"):
            delegation = sourcecraft_module.build_delegation_profile(task, {
                "description": request.description,
                "repo_path": request.repo_path,
                "branch": request.branch,
                "task_type": request.task_type,
                "priority": request.priority,
            })
        route_acceptance = router.route(task) if router else None
        schedule_decision = scheduler.schedule(task) if scheduler else None
        return {
            "status": "ok",
            "sourcecraft": self._sourcecraft_snapshot(),
            "delegation": delegation,
            "task": {
                "task_id": task.task_id,
                "type": task.type.value,
                "priority": task.priority.value,
                "required_capability": task.required_capability,
                "repo_path": task.context.repo_path,
                "branch": task.context.branch,
            },
            "route": route_acceptance.as_dict() if route_acceptance else None,
            "schedule": schedule_decision.as_dict() if schedule_decision else None,
        }

    def _run_server(self) -> None:
        app = FastAPI(title="AI Orchestrator Kernel API")

        @app.get("/health")
        async def health_endpoint():
            return {"status": "ok"}

        @app.get("/api/health")
        async def api_health_endpoint():
            return {"status": "ok"}

        @app.get("/sourcecraft")
        async def sourcecraft_endpoint():
            return self._sourcecraft_snapshot()

        @app.get("/sourcecraft/matrix")
        async def sourcecraft_matrix_endpoint():
            return {"status": "ok", "matrix": self._sourcecraft_matrix()}

        @app.post("/sourcecraft/delegate")
        async def sourcecraft_delegate_endpoint(request: SourceCraftDelegateRequest):
            return self._sourcecraft_delegate(request)

        @app.get("/health/full")
        async def health_full_endpoint():
            return self._health_full_snapshot()

        @app.post("/register_chat")
        async def register_endpoint(request: RegistrationRequest):
            if not self._api:
                return {"status": "error", "message": "Kernel API not available"}

            # Access the Chat Bus module via the Orchestrator
            bus = self._api.get_context("module_manager").get_module("chat_bus")
            if not bus:
                return {"status": "error", "message": "Chat Bus module not loaded"}

            msg = bus.register_interface(  # type: ignore
                provider_id=request.provider_id,
                callback_url=request.callback_url,
                session_id=request.session_id,
            )
            return {"status": "success", "message": msg}

        @app.post("/chat")
        async def chat_endpoint(request: ChatRequest):
            if not self._api:
                return {"status": "error", "message": "Kernel API not available"}

            source_label = request.source or "http_api"
            provider_label = request.provider or "auto"

            payload = {
                "user_id": request.user_id,
                "message": request.message,
                "session_id": request.session_id,
                "source": source_label,
                "provider": provider_label,
            }

            try:
                result = await run_in_threadpool(self._api.submit_user_task, payload, source=source_label)  # type: ignore
                
                agents_used = []
                for r in result.get("results", []):
                    agent_id = r.get("agent_id", "unknown")
                    provider = r.get("provider") or "unknown"
                    model = r.get("model") or "unknown"
                    agents_used.append(f"{agent_id} [{provider} :: {model}]")

                meta_header = "\n".join([
                    "╔══════════════════════════════════════════════════════════════════════╗",
                    "║ 🤖 AI ORCHESTRATOR EXECUTION REPORT                                  ║",
                    "╠══════════════════════════════════════════════════════════════════════╣",
                    f"║ ► Tasks routed to: {', '.join(agents_used)}",
                    "╚══════════════════════════════════════════════════════════════════════╝",
                    ""
                ])

                merged = result.get("merged", {})
                if isinstance(merged, dict) and "summary" in merged:
                    merged["summary"] = meta_header + "\n" + str(merged["summary"])
                elif isinstance(merged, str):
                    merged = meta_header + "\n" + merged

                return {
                    "task_id": result.get("task_id", "unknown"),
                    "status": "completed",
                    "source": source_label,
                    "provider": provider_label,
                    "result": merged if merged else result.get("results", []),
                }
            except Exception as e:
                logger.exception("Error in API Bridge endpoint: %s", e)
                return {"status": "error", "message": str(e)}

        @app.post("/chat/fulltrace")
        async def chat_fulltrace_endpoint(request: ChatRequest):
            source_label = request.source or "http_api"
            provider_label = request.provider or "auto"
            return self._chat_trace_payload(request, source_label=source_label, provider_label=provider_label)

        @app.get("/dump_memory")
        async def dump_memory_endpoint():
            if not self._api:
                return {"status": "error", "message": "Kernel API not available"}
            
            memory = self._api.get_memory()
            if not memory:
                return {"status": "error", "message": "Memory module not found"}
            
            all_keys = memory.list_keys()
            dump = {}
            for key in all_keys:
                # Key format is scope:identifier:actual_key
                parts = key.split(":")
                if len(parts) >= 3:
                    scope, identifier, k = parts[0], parts[1], ":".join(parts[2:])
                    val = memory.get(scope, identifier, k)
                    dump[key] = val
            
            return {"status": "success", "data": dump}

        @app.get("/stats")
        async def stats_endpoint():
            if not self._api:
                return {"status": "error", "message": "Kernel API not available"}
            
            # The API allows us to fetch a module directly if we have access to the orchestrator.
            # But the KernelAPI abstraction might not expose `module_manager`.
            # Let's assume we can get the orchestrator state or the module directly.
            if hasattr(self._api, "get_module"):
                usage_module = self._api.get_module("model_usage")
                if usage_module:
                    return {"status": "success", "data": usage_module.get_statistics()}
                else:
                    return {"status": "error", "message": "Module 'model_usage' is not currently loaded."}
            return {"status": "error", "message": "Cannot access module manager via API."}

        @app.post("/modules/{action}")
        async def manage_module(action: str, request: dict):
            if not self._api:
                return {"status": "error", "message": "Kernel API not available"}
            
            module_name = request.get("module_name")
            if not module_name:
                return {"status": "error", "message": "module_name is required"}
                
            if hasattr(self._api, "load_module") and hasattr(self._api, "unload_module"):
                try:
                    if action == "load":
                        self._api.load_module(module_name)
                        return {"status": "success", "message": f"Module {module_name} loaded successfully."}
                    elif action == "unload":
                        self._api.unload_module(module_name)
                        return {"status": "success", "message": f"Module {module_name} unloaded successfully."}
                    else:
                        return {"status": "error", "message": "Invalid action. Use 'load' or 'unload'."}
                except Exception as e:
                    return {"status": "error", "message": f"Operation failed: {str(e)}"}
            return {"status": "error", "message": "Kernel API does not support dynamic module loading."}

        config = uvicorn.Config(app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        server.run()

    def on_unload(self) -> None:
        if self._api:
            self._api.log("info", f"[API] {self.name} unloading...")
        # Uvicorn doesn't have a trivial way to stop from a thread without more ceremony
        # but since it's a daemon thread, it will exit with the process.

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        pass

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        pass

    def finalize(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "status": "active" if self._server_thread and self._server_thread.is_alive() else "inactive",
        }
