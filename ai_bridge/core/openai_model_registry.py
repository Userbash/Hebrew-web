from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class OpenAIModelCatalog:
    all_models: list[str]
    nano: list[str]
    mini: list[str]
    standard: list[str]
    codex: list[str]
    pro: list[str]
    reasoning: list[str]


class OpenAIModelRegistry:
    def __init__(self) -> None:
        self.cache_path = Path(os.getenv("OPENAI_MODELS_CACHE_PATH", "ai_bridge/.cache/openai_models.json"))
        self.ttl_sec = int(os.getenv("OPENAI_MODELS_CACHE_TTL_SEC", "21600"))

    @staticmethod
    def _api_key() -> str:
        return os.getenv("OPENAI_API_KEY", "").strip()

    @staticmethod
    def _is_text_model(model_id: str) -> bool:
        lowered = model_id.lower()
        if any(token in lowered for token in ("embedding", "moderation", "tts", "whisper", "image", "sora", "dall", "realtime", "audio", "transcribe")):
            return False
        return lowered.startswith(("gpt-", "o", "codex")) or "codex" in lowered

    def _fetch_live(self) -> list[str]:
        key = self._api_key()
        if not key:
            return []
        try:
            from openai import OpenAI

            client = OpenAI(api_key=key)
            models = client.models.list()
        except Exception:
            return []

        out: list[str] = []
        for item in getattr(models, "data", []):
            model_id = str(getattr(item, "id", "")).strip()
            if model_id and self._is_text_model(model_id):
                out.append(model_id)
        return self._dedupe(out)

    @staticmethod
    def _dedupe(models: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for model in models:
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
            return [str(item) for item in payload.get("models", []) if str(item)]
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

    def get_catalog(self, force_refresh: bool = False) -> OpenAIModelCatalog:
        models = self.get_models(force_refresh=force_refresh)
        lower = {model: model.lower() for model in models}
        nano = [model for model, value in lower.items() if "nano" in value]
        mini = [model for model, value in lower.items() if "mini" in value and "codex" not in value]
        codex = [model for model, value in lower.items() if "codex" in value]
        pro = [model for model, value in lower.items() if "pro" in value]
        reasoning = [model for model, value in lower.items() if value.startswith("o") or "reason" in value]
        standard = [model for model in models if model not in set(nano + mini + codex + pro)]
        return OpenAIModelCatalog(models, nano, mini, standard, codex, pro, reasoning)
