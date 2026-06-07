from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from ai_bridge.core.env_loader import load_env_file

logger = logging.getLogger("MistralManager")


class MistralManager:
    def __init__(self, *, api_key: str | None = None) -> None:
        load_env_file()
        load_env_file(".env.bridge")
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.base_url = os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1").rstrip("/")
        self.timeout = self._read_timeout()

    @staticmethod
    def _read_timeout() -> float:
        raw = os.getenv("MISTRAL_PROBE_TIMEOUT_SEC", os.getenv("AI_BRIDGE_PROVIDER_PROBE_TIMEOUT_SEC", "10")).strip()
        try:
            return max(1.0, float(raw))
        except ValueError:
            return 10.0

    def _get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def probe_models(self) -> dict[str, Any]:
        if not self.api_key:
            return {"ok": False, "status_code": None, "models": [], "error": "missing_api_key"}
        try:
            response = httpx.get(f"{self.base_url}/models", headers=self._get_headers(), timeout=self.timeout)
            models: list[str] = []
            if response.status_code == 200:
                data = response.json().get("data", [])
                models = [str(model.get("id", "")).strip() for model in data if str(model.get("id", "")).strip()]
            return {
                "ok": response.status_code == 200,
                "status_code": response.status_code,
                "models": models,
                "error": None if response.status_code == 200 else response.text[:500],
            }
        except Exception as exc:
            return {"ok": False, "status_code": None, "models": [], "error": str(exc)}

    def is_ready(self) -> bool:
        return self.probe_models().get("ok") is True

    def list_models(self) -> list[str]:
        return list(self.probe_models().get("models", []))

    def status(self) -> dict[str, Any]:
        probe = self.probe_models()
        return {"ready": probe.get("ok") is True, "models": probe.get("models", []), "api_probe": probe}
