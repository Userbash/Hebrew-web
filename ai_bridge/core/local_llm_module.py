from __future__ import annotations

import logging
import os
from typing import Any

import requests

from .kernel_protocol import KernelAPI, KernelModule

logger = logging.getLogger("local_llm_module")


class LocalLLMModule(KernelModule):
    def __init__(
        self,
        endpoint: str | None = None,
        model_name: str | None = None,
        timeout_sec: float | None = None,
    ) -> None:
        self.name = "local_llm"
        self.endpoint = (endpoint or os.getenv("AI_BRIDGE_LOCAL_LLM_ENDPOINT") or "http://127.0.0.1:11434").rstrip("/")
        self.model_name = model_name or os.getenv("AI_BRIDGE_LOCAL_LLM_MODEL") or "qwen2.5:32b-instruct-q4_k_m"
        raw_timeout = os.getenv("AI_BRIDGE_LOCAL_LLM_HEALTH_TIMEOUT_SEC")
        if timeout_sec is not None:
            self.timeout_sec = max(0.2, timeout_sec)
        elif raw_timeout:
            try:
                self.timeout_sec = max(0.2, float(raw_timeout))
            except ValueError:
                self.timeout_sec = 1.0
        else:
            self.timeout_sec = 1.0
        self.last_probe: dict[str, Any] = {}

    @staticmethod
    def _model_matches(expected: str, candidate: str) -> bool:
        expected_base = expected.split(":", 1)[0]
        candidate_base = candidate.split(":", 1)[0]
        return candidate == expected or candidate_base == expected_base

    def _probe(self) -> dict[str, Any]:
        response = requests.get(f"{self.endpoint}/api/tags", timeout=self.timeout_sec)
        response.raise_for_status()
        payload = response.json() if response.content else {}
        models = payload.get("models", []) if isinstance(payload, dict) else []
        available_models: list[str] = []
        if isinstance(models, list):
            for item in models:
                if isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str) and name.strip():
                        available_models.append(name.strip())
        model_present = any(self._model_matches(self.model_name, candidate) for candidate in available_models)
        return {
            "ok": True,
            "status_code": response.status_code,
            "available_models": available_models,
            "model_present": model_present,
            "error": None,
        }

    def on_load(self, api: KernelAPI) -> None:
        api.log("info", f"[LOCAL_LLM] Probing Ollama at {self.endpoint} for model {self.model_name}...")
        self.last_probe = self.check_health()
        if self.last_probe.get("ok") and self.last_probe.get("model_present"):
            api.log("info", f"[LOCAL_LLM] Local model {self.model_name} is reachable and ready.")
        elif self.last_probe.get("ok"):
            api.log("warning", f"[LOCAL_LLM] Ollama is reachable, but model {self.model_name} is not loaded yet.")
        else:
            api.log("error", f"[LOCAL_LLM] Local model endpoint is unreachable: {self.last_probe.get('error', 'unknown error')}")

    def on_unload(self) -> None:
        self.last_probe = {}

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        return None

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        return None

    def check_health(self) -> dict[str, Any]:
        try:
            self.last_probe = self._probe()
        except Exception as exc:
            self.last_probe = {
                "ok": False,
                "status_code": None,
                "available_models": [],
                "model_present": False,
                "error": str(exc),
            }
        return self.last_probe

    def finalize(self) -> dict[str, Any]:
        probe = self.last_probe or self.check_health()
        ok = bool(probe.get("ok"))
        model_present = bool(probe.get("model_present"))
        if ok and model_present:
            status = "ready"
        elif ok:
            status = "degraded"
        else:
            status = "error"
        return {
            "status": status,
            "endpoint": self.endpoint,
            "model": self.model_name,
            "health_timeout_sec": self.timeout_sec,
            "service_reachable": ok,
            "model_present": model_present,
            "available_models": probe.get("available_models", []),
            "last_error": probe.get("error"),
        }

    def task_profile(self) -> dict[str, Any]:
        return {
            "agent_type": "local_llm",
            "model": self.model_name,
            "endpoint": self.endpoint,
            "capabilities": ["code", "fix", "refactor", "test", "docs", "research", "review"],
            "primary_tasks": [
                "code generation",
                "bug fixing",
                "refactoring",
                "test generation",
                "documentation",
                "research summaries",
                "review and critique",
            ],
        }
