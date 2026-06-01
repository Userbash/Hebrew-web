from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class IntegrationKind(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    SCHEDULER = "scheduler"
    EVENT_ADAPTER = "event_adapter"
    PROVIDER = "provider"


@dataclass(slots=True)
class IntegrationContext:
    security_gate: Any
    config: dict[str, Any] = field(default_factory=dict)


class IntegrationModule(Protocol):
    name: str
    kind: IntegrationKind
    capabilities: list[str]

    async def initialize(self, context: IntegrationContext) -> None: ...
    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    async def shutdown(self) -> None: ...
