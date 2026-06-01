from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FrontendModule:
    framework: str
    recognizer_api: str
    training_api: str
    enhancement_api: str


class FrontendFrameworkModules:
    def __init__(self) -> None:
        self._modules = {
            "react": FrontendModule("react", "/api/ml/recognize", "/api/ml/train", "/api/ml/enhance-ui"),
            "vue": FrontendModule("vue", "/api/ml/recognize", "/api/ml/train", "/api/ml/enhance-ui"),
            "angular": FrontendModule("angular", "/api/ml/recognize", "/api/ml/train", "/api/ml/enhance-ui"),
            "svelte": FrontendModule("svelte", "/api/ml/recognize", "/api/ml/train", "/api/ml/enhance-ui"),
        }

    def get(self, framework: str) -> FrontendModule:
        key = framework.strip().lower()
        if key not in self._modules:
            raise ValueError(f"unsupported framework: {framework}")
        return self._modules[key]

    def supported(self) -> list[str]:
        return sorted(self._modules.keys())
