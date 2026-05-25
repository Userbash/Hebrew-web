from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import defaultdict
from dataclasses import asdict
from collections.abc import Callable
from typing import Any

from .message_bus import MessageBus
from .models import AckStatus, MessageAck, P2PMessage, TaskEnvelope

logger = logging.getLogger(__name__)

try:
    import aio_pika
except Exception:  # pragma: no cover
    aio_pika = None  # type: ignore[assignment]


class RabbitMQBus(MessageBus):
    def __init__(self, url: str | None = None) -> None:
        super().__init__()
        self.url = (url or os.getenv("AI_BRIDGE_RABBITMQ_URL", "amqp://guest:guest@localhost/")).strip()
        self._connection: Any = None
        self._channel: Any = None
        self._direct_exchange: Any = None
        self._topic_exchange: Any = None
        self._topic_callbacks: dict[str, list[Callable[[Any], None]]] = defaultdict(list)
        self._consumer_tasks: list[asyncio.Task[Any]] = []
        self._enabled = aio_pika is not None

    def publish(self, topic: str, message: Any) -> None:
        if not self._enabled:
            super().publish(topic, message)
            return
        self._run_async(self._publish(topic, message))

    def consume(self, topic: str) -> Any | None:
        if not self._enabled:
            return super().consume(topic)
        return self._run_async_result(self._consume(topic), default=None)

    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> None:
        if not self._enabled:
            super().subscribe(topic, callback)
            return
        self._topic_callbacks[topic].append(callback)
        self._run_async(self._ensure_topic_subscription(topic))

    def send_envelope(self, envelope: TaskEnvelope) -> MessageAck:
        envelope.hop_count += 1
        if envelope.hop_count >= envelope.max_hops:
            logger.error("MaxHops exceeded for TaskEnvelope %s (trace: %s)", envelope.task_id, envelope.trace_id)
            return self.mark_dead_letter_envelope(envelope, "Max hops exceeded")

        routing_key = self.agent_topic(envelope.target_agent) if envelope.target_agent else "orchestrator.inbox"
        if self._enabled:
            self._run_async(self._publish_direct(routing_key, envelope))
        else:
            self.publish(routing_key, envelope)
        return self.ack(envelope.task_id, AckStatus.SENT, envelope.target_agent or "orchestrator")

    def publish_agent_status(self, agent_id: str, payload: dict[str, Any]) -> None:
        topic = f"agent.{agent_id}.status"
        self._publish_topic(topic, payload)

    def publish_session_insights(self, session_id: str, payload: dict[str, Any]) -> None:
        topic = f"session.{session_id}.insights"
        self._publish_topic(topic, payload)

    def _publish_topic(self, topic: str, payload: dict[str, Any]) -> None:
        if self._enabled:
            self._run_async(self._publish_exchange("agents.topic", topic, payload))
        else:
            self.publish(topic, payload)

    async def _connect(self) -> None:
        if not self._enabled:
            return
        if self._channel is not None:
            return
        assert aio_pika is not None
        self._connection = await aio_pika.connect_robust(self.url)
        self._channel = await self._connection.channel()
        self._direct_exchange = await self._channel.declare_exchange("orchestrator.direct", aio_pika.ExchangeType.DIRECT, durable=True)
        self._topic_exchange = await self._channel.declare_exchange("agents.topic", aio_pika.ExchangeType.TOPIC, durable=True)

    async def _publish(self, topic: str, message: Any) -> None:
        await self._publish_exchange("orchestrator.direct", topic, message)

    async def _publish_direct(self, routing_key: str, message: Any) -> None:
        await self._publish_exchange("orchestrator.direct", routing_key, message)

    async def _publish_exchange(self, exchange_name: str, routing_key: str, message: Any) -> None:
        await self._connect()
        if self._channel is None or aio_pika is None:
            return
        exchange = self._direct_exchange if exchange_name == "orchestrator.direct" else self._topic_exchange
        body = json.dumps(self._serialize_message(message), ensure_ascii=True, default=str).encode("utf-8")
        await exchange.publish(aio_pika.Message(body=body), routing_key=routing_key)

    async def _consume(self, topic: str) -> Any | None:
        await self._connect()
        if self._channel is None:
            return None
        queue = await self._channel.declare_queue(topic, durable=True)
        await queue.bind(self._direct_exchange, routing_key=topic)
        incoming = await queue.get(fail=False)
        if incoming is None:
            return None
        async with incoming.process(ignore_processed=True):
            payload = json.loads(incoming.body.decode("utf-8"))
            return payload.get("payload")

    async def _ensure_topic_subscription(self, topic: str) -> None:
        await self._connect()
        if self._channel is None:
            return
        queue = await self._channel.declare_queue(f"sub.{topic}", durable=True)
        await queue.bind(self._topic_exchange, routing_key=topic)

        async def _consume_forever() -> None:
            async with queue.iterator() as iterator:
                async for incoming in iterator:
                    async with incoming.process(ignore_processed=True):
                        payload = json.loads(incoming.body.decode("utf-8"))
                        data = payload.get("payload")
                        for callback in self._topic_callbacks.get(topic, []):
                            callback(data)

        self._consumer_tasks.append(asyncio.create_task(_consume_forever()))

    @staticmethod
    def _serialize_message(message: Any) -> dict[str, Any]:
        if isinstance(message, P2PMessage):
            return {"kind": "p2p", "payload": asdict(message)}
        if isinstance(message, TaskEnvelope):
            return {"kind": "envelope", "payload": asdict(message)}
        return {"kind": "raw", "payload": message}

    @staticmethod
    def _run_async(coro: Any) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            asyncio.run(coro)

    @staticmethod
    def _run_async_result(coro: Any, *, default: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        logger.debug("Async loop already running; returning default for sync call")
        return default
