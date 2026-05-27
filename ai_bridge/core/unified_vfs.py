from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib

from .kernel_api import KernelAPI
from .models import AgentResult, Task, TaskStatus

logger = logging.getLogger("unified_vfs_memory")

class StateIntegrity(str, Enum):
    VALID = "valid"
    CORRUPTED = "corrupted"
    STALE = "stale"
    MISSING = "missing"

@dataclass(slots=True)
class VFSNode:
    path: str
    content: Any
    checksum: str
    last_updated: str
    owner_agent: str
    integrity: StateIntegrity = StateIntegrity.VALID
    metadata: Dict[str, Any] = field(default_factory=dict)

class UnifiedVFSModule:
    """
    Unified Resilient Memory VFS (Virtual File System).
    Provides a shared, validated JSON space for agent synchronization and state recovery.
    """
    name: str = "unified_vfs"
    storage_root: str = "memory_store/vfs"
    
    def __init__(self):
        self._api: KernelAPI | None = None
        self._nodes: Dict[str, VFSNode] = {}
        self._root_path = Path(self.storage_root)

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._root_path.mkdir(parents=True, exist_ok=True)
        self._api.log("info", f"[VFS] {self.name} initialized at {self.storage_root}")
        self._recover_all_states()

    def on_unload(self) -> None:
        self.sync_to_disk()

    def _calculate_checksum(self, content: Any) -> str:
        data = json.dumps(content, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def write_state(self, path: str, content: Any, agent_id: str, metadata: Optional[Dict] = None) -> bool:
        """Atomic write to VFS with integrity tracking."""
        try:
            checksum = self._calculate_checksum(content)
            now = datetime.now(UTC).isoformat()
            
            node = VFSNode(
                path=path,
                content=content,
                checksum=checksum,
                last_updated=now,
                owner_agent=agent_id,
                metadata=metadata or {}
            )
            
            self._nodes[path] = node
            self._persist_node(node)
            
            if self._api:
                self._api.emit_event("VFS_STATE_UPDATE", {"path": path, "agent": agent_id, "checksum": checksum})
            return True
        except Exception as e:
            logger.error(f"VFS Write Failed: {path} -> {e}")
            return False

    def read_state(self, path: str) -> Optional[VFSNode]:
        """Read state from VFS with integrity check."""
        node = self._nodes.get(path)
        if not node:
            # Try to load from disk if not in memory
            node = self._load_node_from_disk(path)
            if not node:
                return None
            self._nodes[path] = node

        # Verify integrity
        current_checksum = self._calculate_checksum(node.content)
        if current_checksum != node.checksum:
            node.integrity = StateIntegrity.CORRUPTED
            if self._api:
                self._api.log("error", f"[VFS] Integrity violation at {path}! Checksum mismatch.")
        
        return node

    def _persist_node(self, node: VFSNode) -> None:
        safe_path = node.path.replace("/", "_").replace("\\", "_")
        file_path = self._root_path / f"{safe_path}.json"
        
        payload = {
            "path": node.path,
            "content": node.content,
            "checksum": node.checksum,
            "last_updated": node.last_updated,
            "owner_agent": node.owner_agent,
            "metadata": node.metadata
        }
        
        file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_node_from_disk(self, path: str) -> Optional[VFSNode]:
        safe_path = path.replace("/", "_").replace("\\", "_")
        file_path = self._root_path / f"{safe_path}.json"
        
        if not file_path.exists():
            return None
            
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return VFSNode(
                path=data["path"],
                content=data["content"],
                checksum=data["checksum"],
                last_updated=data["last_updated"],
                owner_agent=data["owner_agent"],
                metadata=data.get("metadata", {})
            )
        except Exception:
            return None

    def _recover_all_states(self) -> None:
        """Cold boot recovery of all persisted states."""
        for f in self._root_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                node = VFSNode(
                    path=data["path"],
                    content=data["content"],
                    checksum=data["checksum"],
                    last_updated=data["last_updated"],
                    owner_agent=data["owner_agent"],
                    metadata=data.get("metadata", {})
                )
                self._nodes[node.path] = node
            except Exception as e:
                logger.error(f"Failed to recover state from {f}: {e}")

    def sync_to_disk(self) -> None:
        for node in self._nodes.values():
            self._persist_node(node)

    def before_task(self, task: Task, context: Dict[str, Any]) -> None:
        """Handoff logic: try to find resume point in VFS."""
        resume_path = f"active_tasks/{task.task_id}/checkpoint"
        node = self.read_state(resume_path)
        if node and node.integrity == StateIntegrity.VALID:
            # Inject recovered state into task description for the next agent
            context["recovered_state"] = node.content
            if self._api:
                self._api.log("info", f"[VFS] Recovered state for task {task.task_id} from {node.owner_agent}")

    def after_task(self, task: Task, result: AgentResult, context: Dict[str, Any]) -> None:
        """Save terminal state for future recovery or handoff."""
        path = f"active_tasks/{task.task_id}/checkpoint"
        state = {
            "status": result.status.value,
            "output": result.output,
            "intermediate_artifacts": context.get("intermediate_artifacts", []),
            "last_step": context.get("last_step", "completed")
        }
        self.write_state(path, state, result.agent_id)

    def finalize(self) -> Dict[str, Any]:
        return {
            "node_count": len(self._nodes),
            "root": self.storage_root,
            "integrity": "healthy" if all(n.integrity == StateIntegrity.VALID for n in self._nodes.values()) else "degraded"
        }
