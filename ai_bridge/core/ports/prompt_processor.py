from __future__ import annotations
from typing import Protocol
class PromptProcessor(Protocol):
    def process(self, raw_text: str) -> dict[str, object]: ...
