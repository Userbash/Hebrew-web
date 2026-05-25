from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class MemorySettings:
    enabled: bool = False
    database_url: str = ""
    eviction_interval_sec: int = 45
    ram_eviction_threshold: float = 0.70
    hot_cache_max_entries: int = 2000
    retrieval_top_k: int = 8
    command_window_size: int = 12

    @classmethod
    def from_env(cls) -> "MemorySettings":
        return cls(
            enabled=_env_bool("AI_BRIDGE_MEMORY_ENABLED", False),
            database_url=os.getenv("AI_BRIDGE_MEMORY_DATABASE_URL", "").strip(),
            eviction_interval_sec=_env_int("AI_BRIDGE_MEMORY_EVICTION_INTERVAL_SEC", 45),
            ram_eviction_threshold=_env_float("AI_BRIDGE_MEMORY_RAM_THRESHOLD", 0.70),
            hot_cache_max_entries=_env_int("AI_BRIDGE_MEMORY_HOT_CACHE_MAX_ENTRIES", 2000),
            retrieval_top_k=_env_int("AI_BRIDGE_MEMORY_RETRIEVAL_TOP_K", 8),
            command_window_size=_env_int("AI_BRIDGE_MEMORY_COMMAND_WINDOW_SIZE", 12),
        )


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value.strip())
    except ValueError:
        return default
