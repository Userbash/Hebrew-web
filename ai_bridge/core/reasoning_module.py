from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Type, TypeVar, Optional

import instructor
from openai import OpenAI
from pydantic import BaseModel

from .kernel_protocol import KernelAPI, KernelModule
from .models import Task, Complexity

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger("reasoning_module")

@dataclass
class ReasoningModule:
    name: str = "reasoning"
    _api: KernelAPI | None = None
    _client: Any | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        
        # Priority: OpenAI > Antigravity (agy) > Mistral > Local
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = None
        model = "gpt-4o" # default for instructor
        
        if not api_key:
            api_key = os.getenv("ANTIGRAVITY_API_KEY")
            # If using Antigravity, we might need a custom bridge or use the agy CLI.
            # For now, let's assume we can use Mistral as a reliable structured output fallback if OpenAI is missing.
            if not api_key:
                api_key = os.getenv("MISTRAL_API_KEY")
                base_url = "https://api.mistral.ai/v1"
                model = "mistral-large-latest"

        if api_key:
            try:
                self._client = instructor.from_openai(OpenAI(api_key=api_key, base_url=base_url))
                self._api.log("info", f"[REASONING] Module loaded using {model}")
            except Exception as e:
                self._api.log("error", f"[REASONING] Failed to initialize instructor client: {e}")

    def on_unload(self) -> None:
        pass

    def structured_call(self, prompt: str, response_model: Type[T], system_prompt: str = "You are a senior system architect.", model: Optional[str] = None) -> Optional[T]:
        if not self._client:
            return None
        
        try:
            return self._client.chat.completions.create(
                model=model or "gpt-4o",
                response_model=response_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
        except Exception as e:
            logger.error(f"Structured call failed: {e}")
            return None

    def finalize(self) -> dict[str, Any]:
        return {"ready": self._client is not None}
