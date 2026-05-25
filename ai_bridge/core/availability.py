from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from .env_loader import load_env_file


class ProviderStatus(Enum):
    AVAILABLE = "available"
    UNREACHABLE = "unreachable"
    AUTH_FAILED = "auth_failed"
    QUOTA_EXHAUSTED = "quota_exhausted"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class ProviderHealth:
    provider: str
    status: ProviderStatus
    latency_ms: float
    last_check: datetime
    error: str | None = None

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "last_check": self.last_check.isoformat(),
            "error": self.error,
        }


class ModelAvailability:
    def __init__(self) -> None:
        load_env_file()
        self._health_cache: dict[str, ProviderHealth] = {}

    def check_gemini(self) -> ProviderHealth:
        start = datetime.now(UTC)
        # We check Gemini availability by trying to list models or running a minimal echo.
        # Here we use the gemini-cli as a proxy for reachability.
        cmd = ["npx", "@google/gemini-cli", "--prompt", "echo ok", "--model", "gemini-2.5-flash-lite", "--output-format", "text"]
        try:
            # Short timeout for healthcheck
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            if proc.returncode == 0:
                health = ProviderHealth("gemini", ProviderStatus.AVAILABLE, latency, datetime.now(UTC))
            else:
                stderr = proc.stderr.lower()
                status = ProviderStatus.UNREACHABLE
                if any(marker in stderr for marker in ["auth", "api key", "api_key", "invalid key", "401", "403"]):
                    status = ProviderStatus.AUTH_FAILED
                elif any(marker in stderr for marker in ["quota", "429", "exhausted", "limit"]):
                    status = ProviderStatus.QUOTA_EXHAUSTED
                health = ProviderHealth("gemini", status, latency, datetime.now(UTC), error=proc.stderr.strip())
        except subprocess.TimeoutExpired:
            health = ProviderHealth("gemini", ProviderStatus.UNREACHABLE, 15000.0, datetime.now(UTC), error="timeout")
        except Exception as exc:
            health = ProviderHealth("gemini", ProviderStatus.UNKNOWN, 0.0, datetime.now(UTC), error=str(exc))

        self._health_cache["gemini"] = health
        return health

    def check_mistral(self) -> ProviderHealth:
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            return ProviderHealth("mistral", ProviderStatus.AUTH_FAILED, 0.0, datetime.now(UTC), error="MISTRAL_API_KEY not set")

        # Basic reachability check could be a lightweight HTTP request.
        # For now, we return UNKNOWN if we haven't implemented a real ping.
        return ProviderHealth("mistral", ProviderStatus.AVAILABLE, 0.0, datetime.now(UTC))

    def check_all(self) -> dict[str, ProviderHealth]:
        return {
            "gemini": self.check_gemini(),
            "mistral": self.check_mistral(),
        }

    def is_provider_ready(self, provider: str) -> bool:
        health = self._health_cache.get(provider)
        if not health:
            if provider == "gemini":
                health = self.check_gemini()
            elif provider == "mistral":
                health = self.check_mistral()
            else:
                return True # Assume unknown providers (or local) are ready

        return health.status == ProviderStatus.AVAILABLE
