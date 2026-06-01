from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FrontendModule:
    framework: str
    recognizer_api: str
    training_api: str
    enhancement_api: str
    recommended_stack: list[str]


class FrontendFrameworkModules:
    def __init__(self) -> None:
        common = ("/api/ml/recognize", "/api/ml/train", "/api/ml/enhance-ui")
        self._modules = {
            "react": FrontendModule("react", *common, ["react", "vite", "typescript", "tailwindcss", "radix-ui", "shadcn-ui", "react-hook-form", "zod", "tanstack-query", "framer-motion", "lucide-react"]),
            "nextjs": FrontendModule("nextjs", *common, ["next", "typescript", "tailwindcss", "radix-ui", "shadcn-ui", "react-hook-form", "zod", "tanstack-query", "framer-motion"]),
            "vue": FrontendModule("vue", *common, ["vue", "vite", "typescript", "tailwindcss", "pinia", "vue-router", "zod"]),
            "nuxt": FrontendModule("nuxt", *common, ["nuxt", "typescript", "tailwindcss", "pinia"]),
            "angular": FrontendModule("angular", *common, ["angular", "typescript", "rxjs", "angular-material", "ngrx"]),
            "svelte": FrontendModule("svelte", *common, ["sveltekit", "typescript", "tailwindcss", "zod"]),
            "remix": FrontendModule("remix", *common, ["remix", "typescript", "tailwindcss", "zod"]),
            "astro": FrontendModule("astro", *common, ["astro", "typescript", "tailwindcss", "mdx"]),
        }

    def get(self, framework: str) -> FrontendModule:
        key = framework.strip().lower()
        if key not in self._modules:
            raise ValueError(f"unsupported framework: {framework}")
        return self._modules[key]

    def supported(self) -> list[str]:
        return sorted(self._modules.keys())
