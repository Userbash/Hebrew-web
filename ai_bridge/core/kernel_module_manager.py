from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .models import AgentResult, Task


class KernelModule(Protocol):
    name: str

    def on_load(self) -> None: ...

    def on_unload(self) -> None: ...

    def before_task(self, task: Task, context: dict[str, Any]) -> None: ...

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None: ...

    def finalize(self) -> dict[str, Any]: ...


@dataclass(slots=True)
class KernelModuleManager:
    _modules: dict[str, KernelModule] = field(default_factory=dict)
    _loaded: set[str] = field(default_factory=set)

    def register(self, module: KernelModule) -> None:
        self._modules[module.name] = module

    def load(self, name: str) -> None:
        module = self._modules.get(name)
        if module is None:
            raise ValueError(f"Unknown kernel module: {name}")
        if name in self._loaded:
            return
        module.on_load()
        self._loaded.add(name)

    def unload(self, name: str) -> None:
        if name not in self._loaded:
            return
        module = self._modules[name]
        module.on_unload()
        self._loaded.remove(name)

    def is_loaded(self, name: str) -> bool:
        return name in self._loaded

    def loaded_modules(self) -> list[str]:
        return sorted(self._loaded)

    def before_task(self, task: Task, context: dict[str, Any]) -> None:
        for name in self.loaded_modules():
            self._modules[name].before_task(task, context)

    def after_task(self, task: Task, result: AgentResult, context: dict[str, Any]) -> None:
        for name in self.loaded_modules():
            self._modules[name].after_task(task, result, context)

    def finalize(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for name in self.loaded_modules():
            data[name] = self._modules[name].finalize()
        return data
