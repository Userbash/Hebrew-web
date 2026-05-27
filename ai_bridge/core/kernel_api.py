from __future__ import annotations
from typing import Any, Protocol, runtime_checkable
from dataclasses import dataclass

@runtime_checkable
class KernelAPI(Protocol):
    """Internal API exposed to Kernel Modules for safe system interaction."""
    
    def get_context(self, key: str) -> Any: ...
    def emit_event(self, event_name: str, payload: dict[str, Any]) -> None: ...
    def query_state(self, module_name: str, key: str) -> Any: ...
    def log(self, level: str, message: str) -> None: ...
    def get_module(self, name: str) -> Any: ...
    def load_module(self, name: str) -> None: ...
    def unload_module(self, name: str) -> None: ...

@dataclass(slots=True)
class KernelCommunicationLayer:
    """Gateway managing communications between the Orchestrator and Kernel Modules."""
    _api_provider: KernelAPI
    
    def dispatch(self, module_name: str, event_name: str, payload: dict[str, Any]) -> None:
        self._api_provider.emit_event(event_name, {"_from": module_name, **payload})
        self._api_provider.log("info", f"[COMM] Module {module_name} emitted {event_name}")
