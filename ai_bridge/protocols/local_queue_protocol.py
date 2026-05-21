from __future__ import annotations

from ai_bridge.core.message_bus import MessageBus


class LocalQueueProtocol:
    def __init__(self, bus: MessageBus | None = None) -> None:
        self.bus = bus or MessageBus()

    def submit(self, queue: str, message: object) -> None:
        self.bus.publish(queue, message)

    def receive(self, queue: str) -> object | None:
        return self.bus.consume(queue)
