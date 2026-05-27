from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List

from .kernel_protocol import KernelAPI, KernelModule
from .models import Task, AgentResult

logger = logging.getLogger("chat_bus")

@dataclass
class ChatAdapter:
    """Represents an external AI or interface connected to the core."""
    provider_id: str
    callback_url: Optional[str] = None
    session_id: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)

@dataclass
class ChatBusModule:
    """
    Generalized Chat Bus for the Orchestrator Kernel.
    Allows any AI to register as a control channel and receive automated updates.
    """
    name: str = "chat_bus"
    _api: KernelAPI | None = None
    _adapters: Dict[str, ChatAdapter] = field(default_factory=dict)
    _primary_adapter: Optional[str] = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", f"[BUS] {self.name} system online. Ready for AI registration.")

    def register_interface(self, provider_id: str, callback_url: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """Automated registration method for any AI."""
        adapter = ChatAdapter(provider_id=provider_id, callback_url=callback_url, session_id=session_id)
        self._adapters[provider_id] = adapter
        self._primary_adapter = provider_id # Last one registered becomes primary
        
        if self._api:
            self._api.log("info", f"[BUS] AI Provider '{provider_id}' successfully connected via {callback_url or 'direct'}")
        return f"Connected to Core Bus. Primary channel: {provider_id}"

    def on_unload(self) -> None:
        self._adapters.clear()

    def before_task(self, task: Task, context: dict[str, Any]) -> None:
        self._broadcast("task_started", {
            "task_id": task.task_id,
            "type": task.type.value,
            "message": f"Orchestrator began work on: {task.input.description[:50]}..."
        })

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None:
        self._broadcast("task_finished", {
            "task_id": task.task_id,
            "status": result.status.value,
            "summary": result.output.get("summary", "Complete"),
            "confidence": result.confidence
        })

    def _broadcast(self, event: str, payload: dict[str, Any]) -> None:
        """Sends updates to all registered AI interfaces."""
        if not self._api:
            return

        for pid, adapter in self._adapters.items():
            # Emit internal kernel event
            self._api.emit_event(f"bus_{event}", {"provider": pid, **payload})
            
            # In a real production system, here we would trigger an outgoing HTTP request 
            # to adapter.callback_url if provided. 
            if adapter.callback_url:
                # self._trigger_webhook(adapter.callback_url, event, payload)
                pass

    def finalize(self) -> dict[str, Any]:
        return {
            "status": "online",
            "active_adapters": list(self._adapters.keys()),
            "primary": self._primary_adapter
        }
