from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FrontendArchitectureProtocol:
    role: str = "Senior Frontend Architect, UX/UI Designer, Code Quality Reviewer"
    min_quality_score: int = 85

    @property
    def default_stack(self) -> list[str]:
        return [
            "React",
            "TypeScript",
            "Vite",
            "Tailwind CSS",
            "shadcn/ui",
            "lucide-react",
            "framer-motion",
            "TanStack Query",
            "Zustand",
            "React Hook Form",
            "Zod",
        ]

    @property
    def workflow(self) -> list[str]:
        return [
            "analyze task, audience, ux-flow",
            "identify project type and visual style",
            "analyze screenshot/layout weaknesses if provided",
            "build pages map and component map",
            "define design tokens and responsiveness rules",
            "generate modular architecture and typed code",
            "verify a11y: contrast, aria, keyboard, focus",
            "score output: ux, visual, code, originality, a11y, maintainability",
            "auto-refine until score >= 85",
        ]

    @property
    def guardrails(self) -> list[str]:
        return [
            "no template-looking ui",
            "no giant 500+ line components",
            "no random colors outside token system",
            "no mixing business logic/api/ui in one component",
            "no mobile neglect",
            "no completion without quality check",
        ]
