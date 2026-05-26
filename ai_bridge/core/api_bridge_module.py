from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from .kernel_protocol import KernelAPI, KernelModule

logger = logging.getLogger("api_bridge_module")

class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str

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

        @app.post("/chat")
        async def chat_endpoint(request: ChatRequest):
            if not self._api:
                return {"status": "error", "message": "Kernel API not available"}
            
            # Use the Orchestrator's internal method directly!
            # Since we have access to the full Orchestrator instance via KernelAPI (if we cast it)
            # or we can use TaskListener if we want to stick to the queue.
            # However, for true integration, we call orchestrator.submit_user_task
            
            # NOTE: self._api is the Orchestrator instance (see ai_bridge/core/orchestrator.py:101)
            # but we should treat it as KernelAPI. 
            # In ai_bridge/core/orchestrator.py, submit_user_task exists.
            
            payload = {
                "user_id": request.user_id,
                "message": request.message,
                "session_id": request.session_id
            }
            
            try:
                # We need to run this in the orchestrator's event loop or just call it if it's sync.
                # orchestrator.submit_user_task is synchronous (it calls self.run(task) which is sync).
                result = self._api.submit_user_task(payload, source="http_api") # type: ignore
                
                return {
                    "task_id": result.get("task_id", "unknown"),
                    "status": "completed",
                    "result": result.get("merged", result.get("results", []))
                }
            except Exception as e:
                logger.exception("Error in API Bridge endpoint: %s", e)
                return {"status": "error", "message": str(e)}

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
            "status": "active" if self._server_thread and self._server_thread.is_alive() else "inactive"
        }
