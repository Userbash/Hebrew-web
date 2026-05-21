from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from typing import Any


class MessageBus:
    def __init__(self) -> None:
        self._queues: dict[str, deque[Any]] = defaultdict(deque)
        self._subscribers: dict[str, list[Callable[[Any], None]]] = defaultdict(list)

    def publish(self, topic: str, message: Any) -> None:
        self._queues[topic].append(message)
        for callback in self._subscribers[topic]:
            callback(message)

    def consume(self, topic: str) -> Any | None:
        if not self._queues[topic]:
            return None
        return self._queues[topic].popleft()

    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> None:
        self._subscribers[topic].append(callback)

    def depth(self, topic: str) -> int:
        return len(self._queues[topic])
