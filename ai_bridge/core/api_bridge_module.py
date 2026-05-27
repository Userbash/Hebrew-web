from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from .kernel_protocol import KernelAPI, KernelModule

logger = logging.getLogger("api_bridge_module")


class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str


class RegistrationRequest(BaseModel):
    provider_id: str
    callback_url: Optional[str] = None
    session_id: Optional[str] = None


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
        self._api.log("info", f"[API] {self.name} module loading...")

        # We run the FastAPI server in a separate thread to not block the Orchestrator
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

            payload = {
                "user_id": request.user_id,
                "message": request.message,
                "session_id": request.session_id,
            }

            try:
                result = self._api.submit_user_task(payload, source="http_api")  # type: ignore
                
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
                    "result": merged if merged else result.get("results", []),
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
