from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .frontend_architecture_protocol import FrontendArchitectureProtocol
from .frontend_scaffold_generator import FrontendScaffoldGenerator
from .component_codegen_module import ComponentCodegenModule
from .integrations import DesignLearningModule, FrontendFrameworkModules, ImageMLOrchestrator
from .kernel_protocol import KernelAPI, KernelModule
from .session_memory import MemoryScope, SessionMemory


@dataclass(slots=True)
class FrontendEngineeringBridgeModule(KernelModule):
    name: str = "frontend_engineering_bridge"
    _api: KernelAPI | None = None
    _ml: ImageMLOrchestrator | None = None
    _frameworks: FrontendFrameworkModules | None = None
    _learning: DesignLearningModule | None = None
    _protocol: FrontendArchitectureProtocol | None = None
    _scaffold: FrontendScaffoldGenerator | None = None
    _codegen: ComponentCodegenModule | None = None

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        memory = api.get_memory()
        if not isinstance(memory, SessionMemory):
            memory = SessionMemory()
        self._ml = ImageMLOrchestrator()
        self._frameworks = FrontendFrameworkModules()
        self._learning = DesignLearningModule(memory=memory, namespace="frontend_bridge")
        self._protocol = FrontendArchitectureProtocol()
        self._scaffold = FrontendScaffoldGenerator()
        self._codegen = ComponentCodegenModule()
        self._api.log("info", "[FRONTEND_BRIDGE] unified frontend engineering bridge loaded")

    def on_unload(self) -> None:
        self._ml = None
        self._frameworks = None
        self._learning = None
        self._protocol = None
        self._scaffold = None
        self._codegen = None

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        if not (self._frameworks and self._learning):
            return
        framework = str(context.get("framework") or "react").lower()
        try:
            mod = self._frameworks.get(framework)
        except Exception:
            mod = self._frameworks.get("react")
            framework = "react"
        context["frontend_bridge"] = {
            "framework": framework,
            "role": self._protocol.role if self._protocol else "frontend_architect",
            "module": {
                "recognizer_api": mod.recognizer_api,
                "training_api": mod.training_api,
                "enhancement_api": mod.enhancement_api,
            },
            "subsystems": [
                "design_analysis",
                "design_tokens",
                "anti_template_quality",
                "ml_recognition",
                "design_learning",
                "ui_coding_assist",
                "frontend_scaffold_generator",
                "component_codegen_module",
            ],
            "quality_gate": {
                "min_score": self._protocol.min_quality_score if self._protocol else 85,
                "dimensions": ["ux", "visual", "code", "originality", "a11y", "maintainability"],
            },
            "default_stack": self._protocol.default_stack if self._protocol else ["React", "TypeScript"],
            "workflow": self._protocol.workflow if self._protocol else [],
            "guardrails": self._protocol.guardrails if self._protocol else [],
        }
        suggestion = self._learning.suggest_ui_direction(framework)
        context["frontend_bridge"]["suggestion"] = suggestion

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        if not (self._learning and self._api):
            return
        framework = str((context.get("frontend_bridge") or {}).get("framework") or "react")
        summary = ""
        if hasattr(result, "output") and isinstance(getattr(result, "output"), dict):
            summary = str(getattr(result, "output").get("summary", ""))
        score = 0.85 if "unique" in summary.lower() or "brand" in summary.lower() else 0.65
        self._api.get_memory().set(  # type: ignore[call-arg]
            MemoryScope.CAPABILITY,
            "frontend_bridge",
            f"last:{framework}",
            {"summary": summary[:500], "score": score},
        )

    def finalize(self) -> dict[str, Any]:
        frameworks = self._frameworks.supported() if self._frameworks else []
        return {
            "status": "active",
            "frameworks": frameworks,
            "bridge_mode": "kernel_first",
            "subsystems": 8,
            "quality_gate_min": self._protocol.min_quality_score if self._protocol else 85,
        }
