from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MemoryPolicy:
    denylist_keys: set[str] = field(default_factory=lambda: {
        "api_key", "apikey", "token", "password", "secret", "private_key", "refresh_token", "cookie",
    })
    max_entry_size: int = 128_000

    def redact(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            redacted: dict[str, Any] = {}
            for key, value in payload.items():
                key_l = key.lower()
                if any(blocked in key_l for blocked in self.denylist_keys):
                    redacted[key] = "[REDACTED]"
                else:
                    redacted[key] = self.redact(value)
            return redacted
        if isinstance(payload, list):
            return [self.redact(item) for item in payload]
        if isinstance(payload, tuple):
            return tuple(self.redact(item) for item in payload)
        return payload

    def validate_size(self, payload: Any) -> None:
        size = len(str(payload).encode("utf-8"))
        if size > self.max_entry_size:
            raise ValueError(f"Memory entry exceeds max size: {size} > {self.max_entry_size}")
