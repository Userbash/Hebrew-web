from __future__ import annotations
from typing import Protocol, Any
class PluginRuntime(Protocol):
    def invoke(self, plugin_name: str, payload: dict[str, Any]) -> dict[str, Any]: ...
