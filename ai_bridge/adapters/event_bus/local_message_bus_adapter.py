from __future__ import annotations
from typing import Any, Callable
from ai_bridge.core.message_bus import MessageBus

class LocalMessageBusAdapter:
    def __init__(self, bus: MessageBus) -> None:
        self.bus = bus
        self._subs: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        for handler in self._subs.get(topic, []):
            handler(payload)

    def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
        self._subs.setdefault(topic, []).append(handler)
