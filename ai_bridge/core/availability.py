from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover - optional in minimal test envs
    httpx = None  # type: ignore

from .env_loader import load_env_file
from .external_ai_bridge import ExternalAIBridge
from .gemini_runtime_router import GeminiRuntimeRouter
from .gemini_model_registry import GeminiModelRegistry
from .kernel_protocol import KernelAPI


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
    diagnostics: dict[str, Any] = field(default_factory=dict)

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
        if p in {"google", "antigravity", "antigravity-cli", "agy", "gemini-cli", "gemini"}:
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
    def _resolve_gemini_cli_command() -> list[str] | None:
        return ModelAvailability._resolve_antigravity_cli_command()

    @staticmethod
    def _antigravity_runtime_env() -> dict[str, str]:
        return ExternalAIBridge._antigravity_runtime_env()

    @staticmethod
    def _gemini_runtime_env() -> dict[str, str]:
        return ModelAvailability._antigravity_runtime_env()

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
    def _gemini_strategy_profiles() -> dict[str, list[str]]:
        return GeminiRuntimeRouter.strategy_profiles()

    @staticmethod
    def _remediation(provider: str, status: ProviderStatus, diagnostics: dict[str, Any]) -> list[str]:
        steps: list[str] = []
        tcp = diagnostics.get("tcp", {}) if isinstance(diagnostics.get("tcp"), dict) else {}
        if status == ProviderStatus.AUTH_FAILED:
            key_name = "GEMINI_API_KEY/GOOGLE_API_KEY" if provider == "antigravity" else "MISTRAL_API_KEY"
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

    def check_antigravity(self, *, live: bool | None = None) -> ProviderHealth:
        start = datetime.now(UTC)
        diagnostics: dict[str, Any] = {"provider": "antigravity"}
        tcp = self._tcp_probe("antigravity")
        diagnostics["tcp"] = tcp
        diagnostics["auth"] = ExternalAIBridge.antigravity_auth_diagnostics()
        if not tcp.get("ok"):
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            health = ProviderHealth("antigravity", ProviderStatus.TIMEOUT, latency, datetime.now(UTC), error="tcp_probe_failed", diagnostics=diagnostics)
            diagnostics["remediation"] = self._remediation("antigravity", health.status, diagnostics)
            return self._cache(health)

        should_live_probe = self._live_probe_enabled() if live is None else live
        if not should_live_probe:
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            health = ProviderHealth("antigravity", ProviderStatus.DEGRADED, latency, datetime.now(UTC), diagnostics=diagnostics)
            diagnostics["remediation"] = self._remediation("antigravity", health.status, diagnostics)
            return self._cache(health)

        model = os.getenv("ANTIGRAVITY_PROBE_MODEL", os.getenv("GEMINI_PROBE_MODEL", "agy"))
        cli = self._resolve_antigravity_cli_command()
        diagnostics["strategy_profiles"] = self._gemini_strategy_profiles()
        catalog = GeminiModelRegistry().get_catalog(force_refresh=False)
        diagnostics["model_catalog"] = {"all_models": catalog.all_models, "lite": catalog.lite, "flash": catalog.flash, "pro": catalog.pro}
        if not cli:
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            diagnostics["model_probe"] = {"command": None, "model": model, "returncode": None, "stdout_preview": "", "stderr_preview": "antigravity cli not found"}
            health = ProviderHealth("antigravity", ProviderStatus.DEGRADED, latency, datetime.now(UTC), error="antigravity_cli_not_found", diagnostics=diagnostics)
            diagnostics["remediation"] = self._remediation("antigravity", health.status, diagnostics)
            return self._cache(health)

        cmd = [*cli, "-p", "healthcheck: respond with ok"]
        diagnostics["model_probe"] = {"command": " ".join(cli), "model": model}
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self._probe_timeout_sec(), env=self._antigravity_runtime_env(), cwd=os.getcwd())
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            diagnostics["model_probe"].update({"returncode": proc.returncode, "stdout_preview": (proc.stdout or "")[:120], "stderr_preview": (proc.stderr or "")[:240]})
            output_error = ExternalAIBridge._cli_output_error(proc.stdout or "", proc.stderr or "")
            if proc.returncode == 0 and not output_error:
                health = ProviderHealth("antigravity", ProviderStatus.HEALTHY, latency, datetime.now(UTC), diagnostics=diagnostics)
            elif output_error:
                health = ProviderHealth("antigravity", self._status_from_error(output_error), latency, datetime.now(UTC), error=output_error, diagnostics=diagnostics)
            else:
                error = (proc.stderr or proc.stdout or f"non-zero exit code: {proc.returncode}").strip()
                health = ProviderHealth("antigravity", self._status_from_error(error), latency, datetime.now(UTC), error=error, diagnostics=diagnostics)
        except subprocess.TimeoutExpired as exc:
            health = ProviderHealth("antigravity", ProviderStatus.TIMEOUT, self._probe_timeout_sec() * 1000, datetime.now(UTC), error=f"model_probe_timeout: {exc}", diagnostics=diagnostics)
        except Exception as exc:
            health = ProviderHealth("antigravity", self._status_from_error(str(exc), ProviderStatus.DEGRADED), 0.0, datetime.now(UTC), error=str(exc), diagnostics=diagnostics)

        health.diagnostics["remediation"] = self._remediation("antigravity", health.status, health.diagnostics)
        return self._cache(health)


    def check_gemini(self, *, live: bool | None = None) -> ProviderHealth:
        return self.check_antigravity(live=live)

    def check_mistral(self, *, live: bool | None = None) -> ProviderHealth:
        start = datetime.now(UTC)
        diagnostics: dict[str, Any] = {"provider": "mistral"}
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            health = ProviderHealth("mistral", ProviderStatus.AUTH_FAILED, 0.0, datetime.now(UTC), error="MISTRAL_API_KEY not set", diagnostics=diagnostics)
            diagnostics["remediation"] = self._remediation("mistral", health.status, diagnostics)
            return self._cache(health)

        tcp = self._tcp_probe("mistral")
        diagnostics["tcp"] = tcp
        if not tcp.get("ok"):
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            health = ProviderHealth("mistral", ProviderStatus.TIMEOUT, latency, datetime.now(UTC), error="tcp_probe_failed", diagnostics=diagnostics)
            diagnostics["remediation"] = self._remediation("mistral", health.status, diagnostics)
            return self._cache(health)

        should_live_probe = self._live_probe_enabled() if live is None else live
        if not should_live_probe or httpx is None:
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            health = ProviderHealth("mistral", ProviderStatus.DEGRADED if httpx is None else ProviderStatus.HEALTHY, latency, datetime.now(UTC), diagnostics=diagnostics)
            diagnostics["remediation"] = self._remediation("mistral", health.status, diagnostics)
            return self._cache(health)

        try:
            response = httpx.get(
                "https://api.mistral.ai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=self._probe_timeout_sec(),
            )
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            diagnostics["api_probe"] = {"status_code": response.status_code}
            if response.status_code in {401, 403}:
                health = ProviderHealth("mistral", ProviderStatus.AUTH_FAILED, latency, datetime.now(UTC), error=response.text[:240], diagnostics=diagnostics)
            elif response.status_code == 429:
                health = ProviderHealth("mistral", ProviderStatus.QUOTA_EXCEEDED, latency, datetime.now(UTC), error=response.text[:240], diagnostics=diagnostics)
            elif response.status_code >= 500:
                health = ProviderHealth("mistral", ProviderStatus.DEGRADED, latency, datetime.now(UTC), error=response.text[:240], diagnostics=diagnostics)
            else:
                response.raise_for_status()
                health = ProviderHealth("mistral", ProviderStatus.HEALTHY, latency, datetime.now(UTC), diagnostics=diagnostics)
        except Exception as exc:
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            health = ProviderHealth("mistral", self._status_from_error(str(exc), ProviderStatus.DEGRADED), latency, datetime.now(UTC), error=str(exc), diagnostics=diagnostics)

        health.diagnostics["remediation"] = self._remediation("mistral", health.status, health.diagnostics)
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
            "mistral": self.check_mistral(),
        }

    def record_failure(self, provider: str, error_type: str, error: str) -> ProviderHealth:
        normalized = self._normalize_provider(provider)
        if error_type == "auth_fail":
            status = ProviderStatus.AUTH_FAILED
        elif error_type == "quota_exhaustion":
            status = ProviderStatus.QUOTA_EXCEEDED
        elif error_type in {"tcp_timeout", "api_timeout", "sdk_hang"}:
            status = ProviderStatus.TIMEOUT
        else:
            status = ProviderStatus.DEGRADED
        diagnostics = {"provider": normalized, "runtime_failure": {"error_type": error_type, "error": error[:500]}}
        diagnostics["remediation"] = self._remediation(normalized, status, diagnostics)
        return self._cache(ProviderHealth(normalized, status, 0.0, datetime.now(UTC), error=error, diagnostics=diagnostics))

    def is_provider_ready(self, provider: str, *, live: bool | None = None) -> bool:
        provider = self._normalize_provider(provider)
        health = self._health_cache.get(provider)
        if not health:
            health = self.check_provider(provider, live=live)
        return health.status in {ProviderStatus.HEALTHY, ProviderStatus.DEGRADED}

    def cached_report(self) -> dict[str, Any]:
        return {provider: health.as_dict() for provider, health in sorted(self._health_cache.items())}


@dataclass
class ModelAvailabilityModule:
    name: str = "model_availability"
    _api: KernelAPI | None = None
    checks_total: int = 0
    last_task_checks: list[dict[str, Any]] = field(default_factory=list)

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        api.log("info", "[AVAILABILITY] model availability diagnostics loaded")

    def on_unload(self) -> None:
        self._api = None

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        if self._api is None:
            return
        provider = str(context.get("selected_provider") or "")
        availability = self._api.get_context("availability")
        if not provider or not isinstance(availability, ModelAvailability):
            return
        health = availability.check_provider(provider, live=False)
        self.checks_total += 1
        context["availability_preflight"] = health.as_dict()
        self.last_task_checks.append({"task_id": getattr(task, "task_id", None), "provider": provider, "health": health.as_dict()})
        self.last_task_checks = self.last_task_checks[-20:]

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        if self._api is None:
            return
        availability = self._api.get_context("availability")
        provider = str(context.get("provider") or context.get("selected_provider") or "")
        errors = " ".join(str(item) for item in getattr(result, "errors", []) or [])
        if not provider or not errors or not isinstance(availability, ModelAvailability):
            return
        error_type = ExternalAIBridge.classify_error(errors)
        if error_type != "unknown":
            availability.record_failure(provider, error_type, errors)

    def finalize(self) -> dict[str, Any]:
        report: dict[str, Any] = {"checks_total": self.checks_total, "last_task_checks": self.last_task_checks}
        if self._api is not None:
            availability = self._api.get_context("availability")
            if isinstance(availability, ModelAvailability):
                report["providers"] = availability.cached_report()
        return report
