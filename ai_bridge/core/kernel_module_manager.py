from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .kernel_protocol import KernelAPI, KernelModule


@dataclass(slots=True)
class KernelModuleManager:
    _modules: dict[str, KernelModule] = field(default_factory=dict)
    _loaded: set[str] = field(default_factory=set)
    _api: KernelAPI | None = None

    def set_api(self, api: KernelAPI) -> None:
        self._api = api

    def register(self, module: KernelModule) -> None:
        self._modules[module.name] = module

    def load(self, name: str) -> None:
        if self._api is None:
            raise RuntimeError("KernelAPI not initialized in ModuleManager")
        module = self._modules.get(name)
        if not module or name in self._loaded:
            return
        module.on_load(self._api)
        self._loaded.add(name)

    def unload(self, name: str) -> None:
        if name not in self._loaded:
            return
        module = self._modules.get(name)
        if module is None:
            self._loaded.remove(name)
            return
        if hasattr(module, "on_unload"):
            module.on_unload()
        self._loaded.remove(name)


    def get_module(self, name: str) -> KernelModule | None:
        return self._modules.get(name)

    def is_loaded(self, name: str) -> bool:
        return name in self._loaded

    def loaded_modules(self) -> list[str]:
        return sorted(self._loaded)

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        for name in self.loaded_modules():
            module = self._modules[name]
            if hasattr(module, "before_task"):
                module.before_task(task, context)

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        for name in self.loaded_modules():
            module = self._modules[name]
            if hasattr(module, "after_task"):
                module.after_task(task, result, context)

    def finalize(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for name in self.loaded_modules():
            module = self._modules[name]
            if hasattr(module, "finalize"):
                data[name] = module.finalize()
        return data
