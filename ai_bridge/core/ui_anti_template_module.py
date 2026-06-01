from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .kernel_protocol import KernelAPI, KernelModule


@dataclass(slots=True)
class UIAntiTemplateModule(KernelModule):
    name: str = "ui_anti_template"
    _api: KernelAPI | None = None
    _scores: list[float] = field(default_factory=list)

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", "[UI] ui_anti_template module loaded")

    def on_unload(self) -> None:
        self._scores.clear()

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        constraints = context.setdefault("ui_constraints", [])
        constraints.extend(
            [
                "avoid generic card-only layout",
                "introduce brand-specific visual signature",
                "preserve accessibility and contrast",
                "prioritize workflow density over decorative blocks",
            ]
        )

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        summary = ""
        if hasattr(result, "output") and isinstance(getattr(result, "output"), dict):
            summary = str(getattr(result, "output").get("summary", "")).lower()
        penalties = ("template", "boilerplate", "generic")
        score = 1.0 - 0.2 * sum(1 for p in penalties if p in summary)
        score = max(0.0, min(1.0, score))
        self._scores.append(score)

    def finalize(self) -> dict[str, Any]:
        avg = sum(self._scores) / len(self._scores) if self._scores else 1.0
        return {"status": "active", "anti_template_score": round(avg, 3), "samples": len(self._scores)}
