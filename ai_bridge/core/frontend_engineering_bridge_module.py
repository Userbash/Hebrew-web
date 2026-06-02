from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .frontend_architecture_protocol import FrontendArchitectureProtocol
from .frontend_scaffold_generator import FrontendScaffoldGenerator
from .component_codegen_module import ComponentCodegenModule
from .intent_analyzer_module import IntentAnalyzerModule
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
    _analyzer: IntentAnalyzerModule | None = None

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
        self._analyzer = IntentAnalyzerModule()
        self._analyzer.on_load(api)
        self._api.log("info", "[FRONTEND_BRIDGE] unified frontend engineering bridge loaded")

    def on_unload(self) -> None:
        self._ml = None
        self._frameworks = None
        self._learning = None
        self._protocol = None
        self._scaffold = None
        self._codegen = None
        self._analyzer = None

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
                "recommended_stack": mod.recommended_stack,
            },
            "libraries": {
                "ui": ["radix-ui", "shadcn-ui", "lucide-react", "framer-motion"],
                "state_data": ["tanstack-query", "zustand", "redux-toolkit"],
                "forms_validation": ["react-hook-form", "zod", "yup"],
                "styles": ["tailwindcss", "postcss", "sass"],
                "backend_fullstack": ["fastapi", "prisma", "supabase", "stripe", "redis", "celery"],
                "content_automation": ["markdown", "mdx", "headless-cms"],
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
                "content_seed",
                "fullstack_delivery",
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
        if not (self._learning and self._api and self._analyzer):
            return
        framework = str((context.get("frontend_bridge") or {}).get("framework") or "react")
        summary = ""
        if hasattr(result, "output") and isinstance(getattr(result, "output"), dict):
            summary = str(getattr(result, "output").get("summary", ""))
        score = 0.85 if "unique" in summary.lower() or "brand" in summary.lower() else 0.65

        generated: dict[str, Any] = {"status": "skipped"}
        if self._should_codegen(task) and self._scaffold and self._codegen:
            target_root = str(context.get("frontend_output_root") or "frontend-react")
            app_name = str(context.get("frontend_app_name") or "frontend-app")
            
            # Use IntentAnalyzer to get a structured schema
            raw_input = str(getattr(getattr(task, "input", None), "description", ""))
            design_schema = self._analyzer.analyze_user_prompt(raw_input)
            
            scaffold = self._scaffold.generate(target_root, app_name=app_name)
            
            # Convert DesignSchema Pydantic model to dict for ComponentCodegen
            # ComponentCodegen expects a list of dictionaries in 'components' key
            schema_dict = design_schema.model_dump()
            schema_dict["components"] = [{"name": c} for c in design_schema.components]
            
            codegen = self._codegen.generate(target_root, schema_dict)
            
            content_seed = {
                "headline": f"Modern {design_schema.vibe} design",
                "subheadline": f"Based on {design_schema.layout} layout",
                "cta_primary": "Get Started",
                "cta_secondary": "Learn More",
            }
            generated = {"status": "generated", "root": target_root, "scaffold": scaffold, "codegen": codegen, "content_seed": content_seed}
            context["frontend_generated"] = generated

        self._api.get_memory().set(  # type: ignore[call-arg]
            MemoryScope.CAPABILITY,
            "frontend_bridge",
            f"last:{framework}",
            {"summary": summary[:500], "score": score, "generated": generated},
        )


    def _should_codegen(self, task: Any) -> bool:
        t = str(getattr(getattr(task, "type", None), "value", getattr(task, "type", ""))).lower()
        description = getattr(task, "input", None)
        text = str(getattr(description, "description", "")).lower()

        return t in {"code", "plan", "docs"} and any(k in text for k in ["frontend", "ui", "landing", "page", "catalog", "react", "design"])


    @staticmethod
    def _default_schema() -> dict[str, Any]:
        return {
            "components": [
                {"name": "HeroSection"},
                {"name": "CategorySidebar"},
                {"name": "CourseCard"},
                {"name": "FeatureGrid"},
                {"name": "FooterNav"},
            ]
        }

    def finalize(self) -> dict[str, Any]:
        frameworks = self._frameworks.supported() if self._frameworks else []
        return {
            "status": "active",
            "frameworks": frameworks,
            "bridge_mode": "kernel_first",
            "subsystems": 10,
            "quality_gate_min": self._protocol.min_quality_score if self._protocol else 85,
        }
