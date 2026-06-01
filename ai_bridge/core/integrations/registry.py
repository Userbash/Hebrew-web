from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import IntegrationKind, IntegrationModule


@dataclass(slots=True)
class RegisteredIntegration:
    name: str
    kind: IntegrationKind
    capabilities: list[str]
    module: Any


class IntegrationRegistry:
    def __init__(self) -> None:
        self._items: dict[str, RegisteredIntegration] = {}

    def register(self, module: IntegrationModule) -> RegisteredIntegration:
        item = RegisteredIntegration(
            name=module.name,
            kind=module.kind,
            capabilities=sorted(set(module.capabilities)),
            module=module,
        )
        self._items[module.name] = item
        return item

    def get(self, name: str) -> RegisteredIntegration | None:
        return self._items.get(name)

    def list(self) -> list[RegisteredIntegration]:
        return list(self._items.values())
