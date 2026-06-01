from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class KPIEventLogger:
    file_path: Path

    @classmethod
    def from_env(cls) -> "KPIEventLogger":
        configured = (os.getenv("AI_BRIDGE_KPI_LOG_FILE") or "").strip()
        if configured:
            target = Path(configured)
        else:
            base_dir = Path((os.getenv("AI_BRIDGE_MEMORY_STORE_DIR") or "memory_store").strip())
            target = base_dir / "kpi_events.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        return cls(file_path=target)

    def write(self, payload: dict[str, Any]) -> None:
        row = dict(payload)
        row.setdefault("logged_at", datetime.now(UTC).isoformat())
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
