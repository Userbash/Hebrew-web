from __future__ import annotations

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Dict, List

from .models import AgentStatus

logger = logging.getLogger("tpp_p2p_network")

@dataclass
class PodState:
    agent_id: str
    status: AgentStatus
    current_task: str | None
    memory_fingerprint: str
    last_heartbeat: datetime
    capabilities: List[str]

@dataclass
class TPPMessage:
    """Transparent Peer-to-Peer (TPP) Message Protocol"""
    message_id: str
    sender_pod: str
    target_pod: str
    message_type: str  # e.g., 'state_sync', 'memory_share', 'direct_task'
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

class TPPNetwork:
    """
    Implements the Transparent Peer-to-Peer (TPP) protocol.
    Treats Agents as Kubernetes-like Pods that can discover each other
    and share memory/state directly without the Orchestrator bottleneck.
    """
    def __init__(self) -> None:
        self.pods: Dict[str, PodState] = {}
        # Direct sockets/queues for pod-to-pod communication
        self._pod_inboxes: Dict[str, asyncio.Queue] = {}

    def register_pod(self, agent_id: str, capabilities: List[str]) -> None:
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

    def update_state(self, agent_id: str, status: AgentStatus, task: str | None, fingerprint: str) -> None:
        if pod := self.pods.get(agent_id):
            pod.status = status
            pod.current_task = task
            pod.memory_fingerprint = fingerprint
            pod.last_heartbeat = datetime.now(UTC)

    def discover_peers(self, capability: str) -> List[str]:
        """Find other pods that have a specific capability."""
        return [
            pod_id for pod_id, state in self.pods.items()
            if capability in state.capabilities and state.status == AgentStatus.READY
        ]

    async def send_direct(self, message: TPPMessage) -> bool:
        """Direct Pod-to-Pod communication."""
        inbox = self._pod_inboxes.get(message.target_pod)
        if inbox:
            await inbox.put(message)
            logger.debug(f"[TPP] Sent {message.message_type} from {message.sender_pod} to {message.target_pod}")
            return True
        logger.warning(f"[TPP] Target pod {message.target_pod} unreachable")
        return False

    async def receive(self, agent_id: str) -> TPPMessage | None:
        inbox = self._pod_inboxes.get(agent_id)
        if inbox and not inbox.empty():
            return await inbox.get()
        return None

    def broadcast_state(self, sender_id: str) -> None:
        """Gossip protocol: broadcast state to all peers to maintain a distributed ledger."""
        if sender_id not in self.pods:
            return
        state = self.pods[sender_id]
        payload = {
            "status": state.status.value,
            "current_task": state.current_task,
            "memory_fingerprint": state.memory_fingerprint
        }
        for target in self.pods:
            if target != sender_id:
                msg = TPPMessage(
                    message_id=f"sync_{sender_id}_{datetime.now().timestamp()}",
                    sender_pod=sender_id,
                    target_pod=target,
                    message_type="state_sync",
                    payload=payload
                )
                # Fire and forget (fire-and-forget in sync context, but would be async in real event loop)
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.send_direct(msg))
                except RuntimeError:
                    pass
