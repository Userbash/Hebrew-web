from __future__ import annotations

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, UTC
from collections import defaultdict, deque
from collections.abc import Callable
from typing import Any, Dict, List, Optional

from .models import AckStatus, MessageAck, P2PMessage, TaskEnvelope, TaskStatus, AgentStatus

logger = logging.getLogger(__name__)

@dataclass(slots=True)
class PodState:
    agent_id: str
    status: AgentStatus
    current_task: str | None
    memory_fingerprint: str
    last_heartbeat: datetime
    capabilities: List[str]

class MessageBus:
    """
    Transparent Peer-to-Peer (TPP) Message Bus.
    Acts as a distributed mesh where Agents (Pods) communicate directly.
    """
    def __init__(self) -> None:
        self._queues: Dict[str, deque[Any]] = defaultdict(deque)
        self._subscribers: Dict[str, list[Callable[[Any], None]]] = defaultdict(list)
        self._acks: Dict[str, list[MessageAck]] = defaultdict(list)
        self._unacked: Dict[str, Any] = {}
        self.dead_letters: list[Any] = []
        
        # TPP Pod State Management
        self.pods: Dict[str, PodState] = {}
        self._pod_inboxes: Dict[str, asyncio.Queue] = {}

    def register_pod(self, agent_id: str, capabilities: List[str]) -> None:
        """Register a new Agent Pod in the TPP mesh."""
        from datetime import UTC, datetime
        self.pods[agent_id] = PodState(
            agent_id=agent_id,
            status=AgentStatus.READY,
            current_task=None,
            memory_fingerprint="",
            last_heartbeat=datetime.now(UTC),
            capabilities=capabilities
        )
        if agent_id not in self._pod_inboxes:
            self._pod_inboxes[agent_id] = asyncio.Queue()
        logger.info(f"[TPP] Pod registered: {agent_id}")

    def update_pod_state(self, agent_id: str, status: AgentStatus, task: str | None = None, fingerprint: str = "") -> None:
        """Update the shared state of a Pod in the mesh."""
        from datetime import UTC, datetime
        if pod := self.pods.get(agent_id):
            pod.status = status
            pod.current_task = task
            pod.memory_fingerprint = fingerprint
            pod.last_heartbeat = datetime.now(UTC)
            self._gossip_state(agent_id)

    def discover_peers(self, capability: str) -> List[str]:
        """Find other pods in the mesh that have a specific capability."""
        return [
            pod_id for pod_id, state in self.pods.items()
            if capability in state.capabilities and state.status in {AgentStatus.READY, AgentStatus.IDLE}
        ]

    def _gossip_state(self, sender_id: str) -> None:
        """Broadcast state updates to the entire mesh."""
        # In a fully distributed system, this would be a real gossip protocol.
        # Here we simulate it by updating the shared 'pods' dictionary.
        pass

    def publish(self, topic: str, message: Any) -> None:
        self._queues[topic].append(message)
        for callback in self._subscribers[topic]:
            callback(message)

    def consume(self, topic: str) -> Any | None:
        if not self._queues[topic]:
            return None
        msg = self._queues[topic].popleft()
        
        # Track unacked message
        msg_id = getattr(msg, "message_id", getattr(msg, "task_id", None))
        if msg_id:
            self._unacked[msg_id] = msg
            
        return msg

    def send_p2p(self, message: P2PMessage) -> MessageAck:
        """Direct P2P delivery using TPP protocol."""
        topic = self.agent_topic(message.to_agent)
        message.route = message.route or [message.from_agent, message.to_agent]
        message.delivery_mode = "tpp_direct"
        
        # Put in pod's virtual inbox queue if available
        if message.to_agent in self._pod_inboxes:
            try:
                self._pod_inboxes[message.to_agent].put_nowait(message)
            except Exception:
                pass
                
        self.publish(topic, message)
        return self.ack(message.message_id, AckStatus.SENT, message.to_agent)

    def receive_for_agent(self, agent_id: str) -> P2PMessage | TaskEnvelope | None:
        # Check TPP direct inbox first
        if agent_id in self._pod_inboxes:
            try:
                msg = self._pod_inboxes[agent_id].get_nowait()
                if msg:
                    return msg
            except Exception:
                pass
                
        message = self.consume(self.agent_topic(agent_id))
        if isinstance(message, P2PMessage) and message.requires_ack:
            self.ack(message.message_id, AckStatus.RECEIVED, agent_id)
        elif isinstance(message, TaskEnvelope):
            self.ack(message.task_id, AckStatus.RECEIVED, agent_id)
        return message

    def ack(self, message_id: str, status: AckStatus | TaskStatus | str, received_by: str, reason: str | None = None) -> MessageAck:
        ack_status = self._normalize_ack_status(status)
        ack = MessageAck(message_id=message_id, ack_status=ack_status, received_by=received_by, reason=reason)
        self._acks[message_id].append(ack)
        
        if ack_status in {AckStatus.RECEIVED, AckStatus.SENT, AckStatus.FAILED, AckStatus.ACCEPTED}:
            # VFS checkpoint is assumed to have been synced and renamed prior to this call
            self._unacked.pop(message_id, None)
            
        return ack

    @staticmethod
    def _normalize_ack_status(status: AckStatus | TaskStatus | str) -> AckStatus:
        if isinstance(status, AckStatus):
            return status
        raw = status.value if hasattr(status, "value") else str(status)
        if raw in {TaskStatus.DONE.value, TaskStatus.ACCEPTED.value, "delivered"}:
            return AckStatus.ACCEPTED
        if raw in {TaskStatus.FAILED.value, TaskStatus.REJECTED.value}:
            return AckStatus.FAILED
        return AckStatus(raw)

    def ack_history(self, message_id: str) -> list[MessageAck]:
        return list(self._acks[message_id])

    def latest_ack(self, message_id: str) -> MessageAck | None:
        history = self._acks.get(message_id, [])
        return history[-1] if history else None

    def mark_dead_letter(self, message: P2PMessage, reason: str) -> MessageAck:
        self.dead_letters.append(message)
        message.is_dead_letter = True
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
        envelope.is_dead_letter = True
        return self.ack(envelope.task_id, AckStatus.FAILED, "dead_letter_queue", reason)

    @staticmethod
    def agent_topic(agent_id: str) -> str:
        return f"agent.{agent_id}.inbox"
