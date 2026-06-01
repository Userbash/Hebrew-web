from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .kernel_protocol import KernelAPI, KernelModule


@dataclass(slots=True)
class UIDesignSystemModule(KernelModule):
    name: str = "ui_design_system"
    _api: KernelAPI | None = None
    _tokens: dict[str, Any] | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._tokens = {
            "radius": {"card": 8, "input": 12, "button": 12},
            "spacing": {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24},
            "typography": {"hero": 44, "h1": 34, "h2": 24, "body": 16, "caption": 13},
            "interaction": {"focus_ring": True, "keyboard_first": True, "motion_reduced_safe": True},
            "quality": {"avoid_template_layouts": True, "require_brand_signature": True},
        }
        self._api.log("info", "[UI] ui_design_system module loaded")

    def on_unload(self) -> None:
        self._tokens = None

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        if not self._tokens:
            return
        context["ui_design_tokens"] = self._tokens

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        return

    def finalize(self) -> dict[str, Any]:
        return {"status": "active", "tokens": self._tokens or {}}
