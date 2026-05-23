from __future__ import annotations

import logging
from collections import defaultdict, deque
from collections.abc import Callable
from typing import Any

from .models import AckStatus, MessageAck, P2PMessage, TaskEnvelope

logger = logging.getLogger(__name__)

class MessageBus:
    def __init__(self) -> None:
        self._queues: dict[str, deque[Any]] = defaultdict(deque)
        self._subscribers: dict[str, list[Callable[[Any], None]]] = defaultdict(list)
        self._acks: dict[str, list[MessageAck]] = defaultdict(list)
        self.dead_letters: list[Any] = []

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

    def send_p2p(self, message: P2PMessage) -> MessageAck:
        topic = self.agent_topic(message.to_agent)
        message.route = message.route or [message.from_agent, message.to_agent]
        self.publish(topic, message)
        return self.ack(message.message_id, AckStatus.SENT, message.to_agent)

    def relay_p2p(self, message: P2PMessage, nearest_peer: str) -> MessageAck:
        message.delivery_mode = "p2p_relay"
        if not message.route:
            message.route = [message.from_agent]
        if nearest_peer not in message.route:
            message.route.append(nearest_peer)
        if message.to_agent not in message.route:
            message.route.append(message.to_agent)
        return self.send_p2p(message)

    def receive_for_agent(self, agent_id: str) -> P2PMessage | TaskEnvelope | None:
        message = self.consume(self.agent_topic(agent_id))
        if isinstance(message, P2PMessage) and message.requires_ack:
            self.ack(message.message_id, AckStatus.RECEIVED, agent_id)
        elif isinstance(message, TaskEnvelope):
            self.ack(message.task_id, AckStatus.RECEIVED, agent_id)
        return message

    def ack(self, message_id: str, status: AckStatus, received_by: str, reason: str | None = None) -> MessageAck:
        ack = MessageAck(message_id=message_id, ack_status=status, received_by=received_by, reason=reason)
        self._acks[message_id].append(ack)
        return ack

    def ack_history(self, message_id: str) -> list[MessageAck]:
        return list(self._acks[message_id])

    def latest_ack(self, message_id: str) -> MessageAck | None:
        history = self._acks.get(message_id, [])
        return history[-1] if history else None

    def mark_dead_letter(self, message: P2PMessage, reason: str) -> MessageAck:
        self.dead_letters.append(message)
        return self.ack(message.message_id, AckStatus.FAILED, message.to_agent, reason)

    def send_envelope(self, envelope: TaskEnvelope) -> MessageAck:
        """Transport-layer handling of a TaskEnvelope, acting as a network packet router."""
        envelope.hop_count += 1
        
        if envelope.hop_count >= envelope.max_hops:
            logger.error(f"MaxHops exceeded for TaskEnvelope {envelope.task_id} (trace: {envelope.trace_id})")
            return self.mark_dead_letter_envelope(envelope, "Max hops exceeded")
            
        topic = self.agent_topic(envelope.target_agent) if envelope.target_agent else "orchestrator.inbox"
        
        logger.info(f"Routing TaskEnvelope {envelope.task_id} to {topic} (Hop: {envelope.hop_count}/{envelope.max_hops})")
        self.publish(topic, envelope)
        
        return self.ack(envelope.task_id, AckStatus.SENT, envelope.target_agent or "orchestrator")

    def mark_dead_letter_envelope(self, envelope: TaskEnvelope, reason: str) -> MessageAck:
        logger.warning(f"Dead-lettering TaskEnvelope {envelope.task_id} (trace: {envelope.trace_id}): {reason}")
        self.dead_letters.append(envelope)
        return self.ack(envelope.task_id, AckStatus.FAILED, "dead_letter_queue", reason)

    @staticmethod
    def agent_topic(agent_id: str) -> str:
        return f"agent.{agent_id}.inbox"
