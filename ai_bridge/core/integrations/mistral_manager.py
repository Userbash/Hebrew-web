from __future__ import annotations
import os
import logging
import httpx
from typing import Any

logger = logging.getLogger("MistralManager")

class MistralManager:
    def __init__(self, *, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.base_url = "https://api.mistral.ai/v1"

    def _get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def is_ready(self) -> bool:
        if not self.api_key:
            return False
        try:
            response = httpx.get(f"{self.base_url}/models", headers=self._get_headers(), timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        try:
            response = httpx.get(f"{self.base_url}/models", headers=self._get_headers(), timeout=5.0)
            if response.status_code == 200:
                data = response.json().get("data", [])
                return [model["id"] for model in data]
        except Exception:
            pass
        return []

    def status(self) -> dict[str, Any]:
        return {
            "ready": self.is_ready(),
            "models": self.list_models()
        }
