from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

try:
    import httpx
except Exception:  # pragma: no cover - optional in minimal test envs
    httpx = None  # type: ignore

from .gemini_model_registry import AntigravityModelRegistry
from .gemini_runtime_router import AntigravityRuntimeRouter
from .env_loader import load_env_file
from .external_ai_bridge import ExternalAIBridge
from .integrations.antigravity_manager import AntigravityManager
from .integrations.mistral_manager import MistralManager


class ProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    TIMEOUT = "timeout"
    AUTH_FAILED = "auth_failed"
    QUOTA_EXCEEDED = "quota_exceeded"
    OFFLINE = "offline"


@dataclass(slots=True)
class ProviderHealth:
    provider: str
    status: ProviderStatus
    latency_ms: float
    last_check: datetime
    error: str | None = None
    diagnostics: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.diagnostics is None:
            self.diagnostics = {}

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "last_check": self.last_check.isoformat(),
            "error": self.error,
            "diagnostics": self.diagnostics,
        }


class ModelAvailability:
    @staticmethod
    def _normalize_provider(provider: str) -> str:
        p = provider.strip().lower()
        if p in {"antigravity", "antigravity-cli", "agy", "google", "gemini", "gemini-cli"}:
            return "antigravity"
        return p

    def __init__(self) -> None:
        load_env_file()
        self._health_cache: dict[str, ProviderHealth] = {}
        self._failure_cache: dict[str, ProviderHealth] = {}

    @staticmethod
    def _probe_timeout_sec() -> float:
        raw = os.getenv("AI_BRIDGE_PROVIDER_PROBE_TIMEOUT_SEC", "20").strip()
        try:
            return max(1.0, float(raw))
        except ValueError:
            return 5.0

    @staticmethod
    def _live_probe_enabled() -> bool:
        return os.getenv("AI_BRIDGE_LIVE_MODEL_PROBE", "true").strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _resolve_antigravity_cli_command() -> list[str] | None:
        return ExternalAIBridge.resolve_antigravity_cli_command()

    @staticmethod
    def _antigravity_runtime_env() -> dict[str, str]:
        return ExternalAIBridge._antigravity_runtime_env()

    @staticmethod
    def _tcp_targets(provider: str) -> list[tuple[str, int]]:
        if provider == "antigravity":
            raw = os.getenv("ANTIGRAVITY_TCP_PROBE_HOSTS", os.getenv("GEMINI_TCP_PROBE_HOSTS", "antigravity.google:443,generativelanguage.googleapis.com:443,www.googleapis.com:443"))
        elif provider == "mistral":
            raw = os.getenv("MISTRAL_TCP_PROBE_HOSTS", "api.mistral.ai:443")
        else:
            raw = ""

        targets: list[tuple[str, int]] = []
        for item in raw.split(","):
            host_port = item.strip()
            if not host_port:
                continue
            if ":" in host_port:
                host, port_raw = host_port.rsplit(":", 1)
            else:
                host, port_raw = host_port, "443"
            try:
                targets.append((host.strip(), int(port_raw)))
            except ValueError:
                continue
        return targets

    @classmethod
    def _tcp_probe(cls, provider: str) -> dict[str, Any]:
        timeout = cls._probe_timeout_sec()
        targets = cls._tcp_targets(provider)
        results: list[dict[str, Any]] = []
        if not targets:
            return {"ok": True, "skipped": True, "targets": results}

        for host, port in targets:
            started = datetime.now(UTC)
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    latency = (datetime.now(UTC) - started).total_seconds() * 1000
                    results.append({"host": host, "port": port, "ok": True, "latency_ms": latency})
            except socket.timeout as exc:
                results.append({"host": host, "port": port, "ok": False, "error_type": "tcp_timeout", "error": str(exc) or "timeout"})
            except OSError as exc:
                results.append({"host": host, "port": port, "ok": False, "error_type": ExternalAIBridge.classify_error(str(exc)), "error": str(exc)})

        return {"ok": any(item.get("ok") for item in results), "targets": results}

    @staticmethod
    def _status_from_error(raw_error: str, default: ProviderStatus = ProviderStatus.OFFLINE) -> ProviderStatus:
        classified = ExternalAIBridge.classify_error(raw_error)
        if classified == "auth_fail":
            return ProviderStatus.AUTH_FAILED
        if classified == "quota_exhaustion":
            return ProviderStatus.QUOTA_EXCEEDED
        if classified in {"tcp_timeout", "api_timeout", "sdk_hang"}:
            return ProviderStatus.TIMEOUT
        return default

    @staticmethod
    def _antigravity_strategy_profiles() -> dict[str, list[str]]:
        return AntigravityRuntimeRouter.strategy_profiles()

    @staticmethod
    def _remediation(provider: str, status: ProviderStatus, diagnostics: dict[str, Any]) -> list[str]:
        steps: list[str] = []
        tcp = diagnostics.get("tcp", {}) if isinstance(diagnostics.get("tcp"), dict) else {}
        if status == ProviderStatus.AUTH_FAILED:
            key_name = "ANTIGRAVITY_API_KEY/GEMINI_API_KEY/GOOGLE_API_KEY" if provider == "antigravity" else "MISTRAL_API_KEY"
            steps.append(f"Проверь {key_name}: переменная окружения должна быть задана и не просрочена.")
        if status == ProviderStatus.QUOTA_EXCEEDED:
            steps.append("Проверь quota/rate limit у провайдера и временно снизь приоритет этого провайдера в routing policy.")
        if status in {ProviderStatus.TIMEOUT, ProviderStatus.OFFLINE}:
            steps.append("Проверь DNS и TCP egress из среды выполнения до provider API на 443/tcp.")
            steps.append("Проверь proxy/firewall/VPN: соединение должно открываться до host из tcp diagnostics.")
            if provider == "antigravity":
                steps.append("Проверь, что Antigravity CLI (`agy`) установлен/доступен и может выполнить `agy -p`.")
        if tcp and not tcp.get("ok"):
            steps.append("TCP probe не открыл ни одного соединения; fallback до другого провайдера корректен до восстановления сети.")
        return steps

    def _cache(self, health: ProviderHealth) -> ProviderHealth:
        provider = self._normalize_provider(health.provider)
        self._health_cache[provider] = health
        if health.status not in {ProviderStatus.HEALTHY, ProviderStatus.DEGRADED}:
            self._failure_cache[provider] = health
        else:
            self._failure_cache.pop(provider, None)
        return health

    def record_failure(self, provider: str, error_type: str, raw_error: str | None = None) -> ProviderHealth:
        normalized = self._normalize_provider(provider)
        status = self._status_from_error(error_type or raw_error or "", ProviderStatus.OFFLINE)
        health = ProviderHealth(
            normalized,
            status,
            0.0,
            datetime.now(UTC),
            error=raw_error or error_type,
            diagnostics={"error_type": error_type, "recorded": True},
        )
        return self._cache(health)

    def is_provider_ready(self, provider: str) -> bool:
        normalized = self._normalize_provider(provider)
        health = self._health_cache.get(normalized)
        if not health:
            return False
        return health.status == ProviderStatus.HEALTHY

    def check_antigravity(self, *, live: bool | None = None) -> ProviderHealth:
        start = datetime.now(UTC)
        diagnostics: dict[str, Any] = {"provider": "antigravity"}
        tcp = self._tcp_probe("antigravity")
        diagnostics["tcp"] = tcp
        
        if not tcp.get("ok"):
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            health = ProviderHealth("antigravity", ProviderStatus.TIMEOUT, latency, datetime.now(UTC), error="tcp_probe_failed", diagnostics=diagnostics)
            diagnostics["remediation"] = self._remediation("antigravity", health.status, diagnostics)
            return self._cache(health)

        manager = AntigravityManager()
        ready = manager.is_ready()
        models = manager.list_models()
        diagnostics["models"] = models
        
        latency = (datetime.now(UTC) - start).total_seconds() * 1000
        
        if ready:
            health = ProviderHealth("antigravity", ProviderStatus.HEALTHY, latency, datetime.now(UTC), diagnostics=diagnostics)
        else:
            error = "antigravity_not_ready"
            health = ProviderHealth("antigravity", ProviderStatus.DEGRADED, latency, datetime.now(UTC), error=error, diagnostics=diagnostics)
            diagnostics["remediation"] = self._remediation("antigravity", health.status, diagnostics)
            
        return self._cache(health)

    def check_gemini(self, *, live: bool | None = None) -> ProviderHealth:
        # Legacy compatibility path retained for older call sites.
        return self.check_antigravity(live=live)

    def check_mistral(self, *, live: bool | None = None) -> ProviderHealth:
        start = datetime.now(UTC)
        diagnostics: dict[str, Any] = {"provider": "mistral"}
        
        # 1. TCP connectivity probe
        tcp = self._tcp_probe("mistral")
        diagnostics["tcp"] = tcp
        if not tcp.get("ok"):
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            health = ProviderHealth("mistral", ProviderStatus.TIMEOUT, latency, datetime.now(UTC), error="tcp_probe_failed", diagnostics=diagnostics)
            diagnostics["remediation"] = self._remediation("mistral", health.status, diagnostics)
            return self._cache(health)

        # 2. Functional/Auth probe using MistralManager
        manager = MistralManager()
        ready = manager.is_ready()
        models = manager.list_models()
        diagnostics["models"] = models
        
        latency = (datetime.now(UTC) - start).total_seconds() * 1000
        
        if ready:
            health = ProviderHealth("mistral", ProviderStatus.HEALTHY, latency, datetime.now(UTC), diagnostics=diagnostics)
        else:
            error = "mistral_auth_failed" if not manager.api_key else "mistral_not_ready"
            health = ProviderHealth("mistral", ProviderStatus.DEGRADED, latency, datetime.now(UTC), error=error, diagnostics=diagnostics)
            diagnostics["remediation"] = self._remediation("mistral", health.status, diagnostics)
            
        return self._cache(health)

    def check_provider(self, provider: str, *, live: bool | None = None) -> ProviderHealth:
        normalized = self._normalize_provider(provider)
        if normalized == "antigravity":
            return self.check_antigravity(live=live)
        if normalized == "mistral":
            return self.check_mistral(live=live)
        health = ProviderHealth(normalized, ProviderStatus.HEALTHY, 0.0, datetime.now(UTC), diagnostics={"provider": normalized, "probe": "local_provider_assumed_ready"})
        return self._cache(health)

    def check_all(self) -> dict[str, ProviderHealth]:
        return {
            "antigravity": self.check_antigravity(),
            "mistral": self.check_mistral()
        }

    def cached_report(self) -> dict[str, dict]:
        return {provider: health.as_dict() for provider, health in sorted(self._health_cache.items())}

class ModelAvailabilityModule:
    name: str = "model_availability"
    def __init__(self):
        pass
    def on_load(self, api):
        pass
    def before_task(self, task, context):
        pass


