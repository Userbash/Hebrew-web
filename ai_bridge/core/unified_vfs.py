from __future__ import annotations

import json
import logging
import hashlib
import os
import fcntl
import tempfile
import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import Lock

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

class ProcessFileLock:
    """Inter-process reader-writer lock using fcntl."""
    def __init__(self, path: Path):
        self.lock_path = path.with_suffix('.lock')
        self.fd = None

    def acquire_write(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o666)
        fcntl.flock(self.fd, fcntl.LOCK_EX)

    def acquire_read(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o666)
        fcntl.flock(self.fd, fcntl.LOCK_SH)

    def release(self):
        if self.fd is not None:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        self.acquire_write()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

class JournalLogger:
    """WAL-like journaling for VFS."""
    def __init__(self, journal_path: Path):
        self.journal_path = journal_path
        self.lock = Lock()

    def append(self, tx_id: str, action: str, path: str, checksum: str):
        with self.lock:
            with open(self.journal_path, "a", encoding="utf-8") as f:
                record = {
                    "tx_id": tx_id,
                    "action": action,
                    "path": path,
                    "checksum": checksum,
                    "ts": datetime.now(UTC).isoformat()
                }
                f.write(json.dumps(record) + "\n")
                f.flush()
                os.fsync(f.fileno())

def fsync_dir(dir_path: Path):
    if hasattr(os, "O_DIRECTORY"):
        try:
            fd = os.open(str(dir_path), os.O_RDONLY | os.O_DIRECTORY)
            os.fsync(fd)
            os.close(fd)
        except OSError:
            pass

def atomic_write(file_path: Path, data: bytes):
    dir_path = file_path.parent
    dir_path.mkdir(parents=True, exist_ok=True)
    temp_path = file_path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    
    with open(temp_path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    
    os.replace(temp_path, file_path)
    fsync_dir(dir_path)

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
        self._artifacts_path = self._root_path / "artifacts"
        self._journal_path = self._root_path / "journal.wal"
        self._journal = JournalLogger(self._journal_path)
        self._memory_lock = Lock()

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._root_path.mkdir(parents=True, exist_ok=True)
        self._artifacts_path.mkdir(parents=True, exist_ok=True)
        if self._api:
            self._api.log("info", f"[VFS] {self.name} initialized at {self.storage_root}")
        self._recover_all_states()

    def on_unload(self) -> None:
        pass

    def _calculate_checksum(self, content: Any) -> str:
        data = json.dumps(content, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def _extract_artifacts(self, content: Any) -> Any:
        if not isinstance(content, dict):
            return content
            
        new_content = content.copy()
        if "output" in new_content and isinstance(new_content["output"], dict):
            for key in ["summary", "diff", "raw_response", "markdown"]:
                val = new_content["output"].get(key)
                if isinstance(val, str) and len(val) > 2048:
                    data_bytes = val.encode("utf-8")
                    artifact_hash = hashlib.sha256(data_bytes).hexdigest()
                    artifact_path = self._artifacts_path / f"{artifact_hash}.bin"
                    if not artifact_path.exists():
                        atomic_write(artifact_path, data_bytes)
                    new_content["output"][key] = {"$vfs_artifact": f"artifacts/{artifact_hash}.bin"}
        return new_content

    def _inject_artifacts(self, content: Any) -> Any:
        if not isinstance(content, dict):
            return content
            
        new_content = content.copy()
        if "output" in new_content and isinstance(new_content["output"], dict):
            for key, val in list(new_content["output"].items()):
                if isinstance(val, dict) and "$vfs_artifact" in val:
                    artifact_path = self._root_path / val["$vfs_artifact"]
                    if artifact_path.exists():
                        with open(artifact_path, "rb") as f:
                            new_content["output"][key] = f.read().decode("utf-8")
        return new_content

    def write_state(self, path: str, content: Any, agent_id: str, metadata: Optional[Dict] = None) -> bool:
        """Atomic write to VFS with WAL and integrity tracking."""
        safe_path = path.replace("/", "_").replace("\\", "_")
        file_path = self._root_path / f"{safe_path}.json"
        
        content_extracted = self._extract_artifacts(content)
        checksum = self._calculate_checksum(content_extracted)
        now = datetime.now(UTC).isoformat()
        
        payload = {
            "path": path,
            "content": content_extracted,
            "checksum": checksum,
            "last_updated": now,
            "owner_agent": agent_id,
            "metadata": metadata or {}
        }
        
        payload_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        tx_id = uuid.uuid4().hex
        self._journal.append(tx_id, "WRITE", path, checksum)
        
        try:
            with ProcessFileLock(file_path):
                atomic_write(file_path, payload_bytes)
            
            self._journal.append(tx_id, "COMMIT", path, checksum)
            
            node = VFSNode(
                path=path,
                content=content_extracted,
                checksum=checksum,
                last_updated=now,
                owner_agent=agent_id,
                metadata=metadata or {}
            )
            with self._memory_lock:
                self._nodes[path] = node
                
            if self._api:
                self._api.emit_event("VFS_STATE_UPDATE", {"path": path, "agent": agent_id, "checksum": checksum})
            return True
        except Exception as e:
            logger.error(f"VFS Write Failed: {path} -> {e}")
            self._journal.append(tx_id, "ROLLBACK", path, checksum)
            return False

    def read_state(self, path: str) -> Optional[VFSNode]:
        """Read state from VFS with integrity check."""
        with self._memory_lock:
            node = self._nodes.get(path)
            
        if not node:
            node = self._load_node_from_disk(path)
            if not node:
                return None
            with self._memory_lock:
                self._nodes[path] = node

        current_checksum = self._calculate_checksum(node.content)
        if current_checksum != node.checksum:
            node.integrity = StateIntegrity.CORRUPTED
            if self._api:
                self._api.log("error", f"[VFS] Integrity violation at {path}! Checksum mismatch. Initiating rollback...")
            return self._recover_from_corruption(path)
        
        node_copy = replace(node, content=self._inject_artifacts(node.content))
        return node_copy

    def _recover_from_corruption(self, path: str) -> Optional[VFSNode]:
        """Handles auto-rollback by relying on previous snapshot or failing."""
        # Simple rollback: mark missing as we don't have multi-versioning yet,
        # but DLQ in message bus will resend the task if no valid checkpoint exists.
        safe_path = path.replace("/", "_").replace("\\", "_")
        file_path = self._root_path / f"{safe_path}.json"
        logger.error(f"State corrupted for {path}. Removing corrupted checkpoint.")
        try:
            with ProcessFileLock(file_path):
                if file_path.exists():
                    os.remove(file_path)
        except OSError:
            pass
            
        with self._memory_lock:
            if path in self._nodes:
                del self._nodes[path]
        return None

    def _load_node_from_disk(self, path: str) -> Optional[VFSNode]:
        safe_path = path.replace("/", "_").replace("\\", "_")
        file_path = self._root_path / f"{safe_path}.json"
        
        if not file_path.exists():
            return None
            
        try:
            with ProcessFileLock(file_path):
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

    def before_task(self, task: Task, context: Dict[str, Any]) -> None:
        """Handoff logic: try to find resume point in VFS."""
        resume_path = f"active_tasks/{task.task_id}/checkpoint"
        node = self.read_state(resume_path)
        if node and node.integrity == StateIntegrity.VALID:
            context["recovered_state"] = node.content
            if self._api:
                self._api.log("info", f"[VFS] Recovered state for task {task.task_id} from {node.owner_agent}")

    def after_task(self, task: Task, result: AgentResult, context: Dict[str, Any]) -> None:
        """Save terminal state for future recovery or handoff."""
        path = f"active_tasks/{task.task_id}/checkpoint"
        output = result.output.as_dict() if hasattr(result.output, "as_dict") else result.output
        state = {
            "status": result.status.value,
            "output": output,
            "intermediate_artifacts": context.get("intermediate_artifacts", []),
            "last_step": context.get("last_step", "completed")
        }
        # In this refactoring, checkpoint MUST be written BEFORE RabbitMQ ack
        # which is handled by orchestrator calling this before acknowledging the task envelop.
        self.write_state(path, state, result.agent_id)

    def finalize(self) -> Dict[str, Any]:
        return {
            "node_count": len(self._nodes),
            "root": self.storage_root,
            "integrity": "healthy" if all(n.integrity == StateIntegrity.VALID for n in self._nodes.values()) else "degraded"
        }
