import json
import logging
import hashlib
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class MemoryHealthChecker:
    def __init__(self, storage_dir: str = "/app/memory_store"):
        self.storage_dir = Path(storage_dir)

    def run_integrity_check(self) -> dict[str, Any]:
        """Verify the integrity and optimization status of the memory store."""
        results = {
            "total_files": 0,
            "corrupted_files": 0,
            "optimization_score": 0.0,
            "integrity_passed": True
        }
        
        memories_path = self.storage_dir / "memories"
        if not memories_path.exists():
            return {"error": "Storage directory not found"}

        files = list(memories_path.glob("*.json"))
        results["total_files"] = len(files)
        
        if results["total_files"] == 0:
            return results

        valid_files = 0
        for f in files:
            try:
                with open(f, "r") as file:
                    data = json.load(file)
                    # Integrity: simple schema check
                    if "session_id" in data and "content" in data:
                        valid_files += 1
                    else:
                        results["corrupted_files"] += 1
            except Exception:
                results["corrupted_files"] += 1

        results["integrity_passed"] = results["corrupted_files"] == 0
        results["optimization_score"] = (valid_files / results["total_files"]) * 100
        
        logger.info(f"[HEALTH] Memory Check: {results}")
        return results

    def get_memory_stats(self) -> dict[str, Any]:
        """Return raw stats about memory utilization."""
        # This could be extended to track hit/miss ratios if integrated with HybridMemory
        return {"storage_path": str(self.storage_dir), "status": "active"}
