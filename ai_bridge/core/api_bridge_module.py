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
from pydantic import BaseModel

from .kernel_protocol import KernelAPI, KernelModule

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


class DesignAuditRequest(BaseModel):
    url: Optional[str] = None
    output_dir: Optional[str] = None


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

        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()
        self._api.log("info", f"[API] {self.name} server started on {self.host}:{self.port}")

    def _run_server(self) -> None:
        app = FastAPI(title="AI Orchestrator Kernel API")

        @app.get("/health")
        async def health_endpoint():
            return {"status": "ok"}

        @app.get("/api/health")
        async def api_health_endpoint():
            return {"status": "ok"}

        @app.get("/status")
        async def status_endpoint():
            if not self._api:
                return {"status": "error", "message": "Kernel API not available"}

            module_manager = self._api.get_context("module_manager")
            registry = self._api.get_context("registry")
            local_llm_module = module_manager.get_module("local_llm") if hasattr(module_manager, "get_module") else None
            testing_module = module_manager.get_module("testing") if hasattr(module_manager, "get_module") else None
            vision_module = module_manager.get_module("vision_design_audit") if hasattr(module_manager, "get_module") else None
            design_learning_module = module_manager.get_module("design_learning") if hasattr(module_manager, "get_module") else None

            local_llm = local_llm_module.finalize() if local_llm_module and hasattr(local_llm_module, "finalize") else {}
            local_llm_profile = local_llm_module.task_profile() if local_llm_module and hasattr(local_llm_module, "task_profile") else {}
            testing = testing_module.status() if testing_module and hasattr(testing_module, "status") else {}
            testing_final = testing_module.finalize() if testing_module and hasattr(testing_module, "finalize") else {}
            design_audit = vision_module.finalize() if vision_module and hasattr(vision_module, "finalize") else {}
            design_learning = design_learning_module.finalize() if design_learning_module and hasattr(design_learning_module, "finalize") else {}

            agents: list[dict[str, Any]] = []
            if registry and hasattr(registry, "list_agents"):
                for agent in registry.list_agents():
                    if getattr(agent, "provider", None) == "local" or "local" in str(getattr(agent, "model_name", "")).lower():
                        agents.append(
                            {
                                "id": agent.id,
                                "type": agent.agent_type,
                                "provider": agent.provider,
                                "model_name": agent.model_name,
                                "capabilities": list(agent.capabilities),
                                "critical": agent.critical,
                            }
                        )

            return {
                "status": "ok",
                "local_llm": local_llm,
                "local_llm_profile": local_llm_profile,
                "testing": testing,
                "testing_final": testing_final,
                "vision_design_audit": design_audit,
                "design_learning": design_learning,
                "local_agents": agents,
            }

        @app.post("/design-audit")
        async def design_audit_endpoint(request: DesignAuditRequest):
            if not self._api:
                return {"status": "error", "message": "Kernel API not available"}
            try:
                result = await run_in_threadpool(
                    self._api.run_design_audit,
                    request.url,
                    request.output_dir or "test-results",
                )  # type: ignore
                return {"status": "ok", "result": result}
            except Exception as exc:
                return {"status": "error", "message": str(exc)}

        @app.post("/register_chat")
        async def register_endpoint(request: RegistrationRequest):
            if not self._api:
                return {"status": "error", "message": "Kernel API not available"}

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
                return {
                    "task_id": result.get("task_id", "unknown"),
                    "status": "completed",
                    "source": source_label,
                    "provider": provider_label,
                    "result": result.get("merged", result.get("results", [])),
                }
            except Exception as e:
                logger.exception("Error in API Bridge endpoint: %s", e)
                return {"status": "error", "message": str(e)}

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
