from __future__ import annotations

import json
import os
import time
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


@dataclass(slots=True)
class AntigravityModelCatalog:
    all_models: list[str]
    lite: list[str]
    flash: list[str]
    pro: list[str]
    thinking: list[str] = field(default_factory=list)


class AntigravityModelRegistry:
    def __init__(self) -> None:
        self.api_base = os.getenv("ANTIGRAVITY_MODELS_API", os.getenv("GEMINI_MODELS_API", "https://generativelanguage.googleapis.com/v1beta/models"))
        self.cache_path = Path(os.getenv("ANTIGRAVITY_MODELS_CACHE_PATH", os.getenv("GEMINI_MODELS_CACHE_PATH", "ai_bridge/.cache/antigravity_models.json")))
        self.ttl_sec = int(os.getenv("ANTIGRAVITY_MODELS_CACHE_TTL_SEC", os.getenv("GEMINI_MODELS_CACHE_TTL_SEC", "21600")))

    def _api_key(self) -> str:
        return os.getenv("ANTIGRAVITY_API_KEY", "").strip() or os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()

    def _fetch_live(self) -> list[str]:
        # Try fetching via agy CLI first as a reliable local source
        try:
            result = subprocess.run(["agy", "models"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Map the CLI output to the expected model format if necessary
                return [line.strip().replace(" ", "-").lower() for line in result.stdout.splitlines() if line.strip()]
        except Exception:
            pass

        key = self._api_key()
        if not key:
            return []
        out: list[str] = []
        page_token = ""
        while True:
            params = {"key": key}
            if page_token:
                params["pageToken"] = page_token
            url = f"{self.api_base}?{urlencode(params)}"
            with urlopen(url, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            for item in payload.get("models", []):
                name = str(item.get("name", "")).replace("models/", "")
                methods = set(item.get("supportedGenerationMethods", []))
                if name and "generateContent" in methods:
                    out.append(name)
            page_token = payload.get("nextPageToken", "")
            if not page_token:
                break
        seen: set[str] = set()
        deduped: list[str] = []
        for model in out:
            if model in seen:
                continue
            seen.add(model)
            deduped.append(model)
        return deduped

    def _load_cache(self) -> list[str]:
        if not self.cache_path.exists():
            return []
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            ts = int(payload.get("ts", 0))
            if int(time.time()) - ts > self.ttl_sec:
                return []
            return [str(x) for x in payload.get("models", []) if str(x)]
        except Exception:
            return []

    def _save_cache(self, models: list[str]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps({"ts": int(time.time()), "models": models}, ensure_ascii=True), encoding="utf-8")

    def get_models(self, force_refresh: bool = False) -> list[str]:
        if not force_refresh:
            cached = self._load_cache()
            if cached:
                return cached
        live = self._fetch_live()
        if live:
            self._save_cache(live)
            return live
        return self._load_cache()

    def get_catalog(self, force_refresh: bool = False) -> AntigravityModelCatalog:
        models = self.get_models(force_refresh=force_refresh)
        lite = [m for m in models if "lite" in m]
        flash = [m for m in models if "flash" in m and "lite" not in m]
        pro = [m for m in models if "pro" in m or ("claude-sonnet" in m and "thinking" not in m)]
        thinking = [m for m in models if "thinking" in m or "claude-opus" in m]
        return AntigravityModelCatalog(models, lite, flash, pro, thinking)


# Legacy compatibility aliases. Keep imports working while the runtime moves to Antigravity.
GeminiModelCatalog = AntigravityModelCatalog
GeminiModelRegistry = AntigravityModelRegistry
