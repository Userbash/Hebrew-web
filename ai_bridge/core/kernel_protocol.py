from __future__ import annotations
from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class KernelAPI(Protocol):
    """
    Standardized Internal API for Kernel Modules.
    Provides secure, read-only access to orchestrator services
    and a structured mechanism for event emission.
    """
    
    def get_context(self, key: str) -> Any:
        """Retrieve system context/orchestrator attributes safely."""
        ...

    def emit_event(self, event_name: str, payload: dict[str, Any]) -> None:
        """Emit system-wide events for monitoring and logging."""
        ...

    def query_module_state(self, module_name: str, key: str) -> Any:
        """Query the finalized state of another module."""
        ...

    def log(self, level: str, message: str) -> None:
        """System-wide logging for module activities."""
        ...

    def get_memory(self) -> Any:
        """Retrieve the primary memory module (SessionMemory)."""
        ...

class KernelModule(Protocol):
    """
    Standardized Protocol for Kernel Modules with mandatory lifecycle hooks.
    """
    name: str

    def on_load(self, api: KernelAPI) -> None:
        """Lifecycle hook: Called when module is registered/loaded."""
        ...

    def on_unload(self) -> None:
        """Lifecycle hook: Called when module is disabled/unloaded."""
        ...

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        """Lifecycle hook: Pre-task interceptor."""
        ...

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        """Lifecycle hook: Post-task interceptor."""
        ...

    def finalize(self) -> dict[str, Any]:
        """Finalize state and return summary for orchestration reporting."""
        ...
