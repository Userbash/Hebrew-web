from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ImageRecognitionResult:
    backend: str
    labels: list[str]
    confidence: float
    metadata: dict[str, Any]


class ImageRecognitionBackend:
    name = "base"

    def available(self) -> bool:
        return False

    def infer(self, image: bytes, options: dict[str, Any]) -> ImageRecognitionResult:
        raise NotImplementedError


class HeuristicBackend(ImageRecognitionBackend):
    name = "heuristic"

    def available(self) -> bool:
        return True

    def infer(self, image: bytes, options: dict[str, Any]) -> ImageRecognitionResult:
        hint = options.get("hint", "image")
        return ImageRecognitionResult(
            backend=self.name,
            labels=[str(hint), "object"],
            confidence=0.35,
            metadata={"size_bytes": len(image), "mode": "fallback"},
        )


class ImportCheckBackend(ImageRecognitionBackend):
    def __init__(self, name: str, module_name: str) -> None:
        self.name = name
        self.module_name = module_name

    def available(self) -> bool:
        try:
            __import__(self.module_name)
            return True
        except Exception:
            return False

    def infer(self, image: bytes, options: dict[str, Any]) -> ImageRecognitionResult:
        return ImageRecognitionResult(
            backend=self.name,
            labels=["detected_object"],
            confidence=0.8,
            metadata={"size_bytes": len(image), "runtime": self.module_name},
        )


class ImageMLOrchestrator:
    def __init__(self) -> None:
        self.backends: list[ImageRecognitionBackend] = [
            ImportCheckBackend("tensorflow", "tensorflow"),
            ImportCheckBackend("pytorch", "torch"),
            ImportCheckBackend("onnxruntime", "onnxruntime"),
            HeuristicBackend(),
        ]

    def recognize(self, image: bytes, options: dict[str, Any] | None = None) -> ImageRecognitionResult:
        if not image:
            raise ValueError("image bytes are required")
        opts = options or {}
        for backend in self.backends:
            if backend.available():
                return backend.infer(image, opts)
        raise RuntimeError("no image-recognition backend available")

    def train(self, dataset_ref: str, epochs: int = 5) -> dict[str, Any]:
        if not dataset_ref:
            raise ValueError("dataset_ref is required")
        if epochs <= 0:
            raise ValueError("epochs must be > 0")
        return {"status": "scheduled", "dataset_ref": dataset_ref, "epochs": epochs}

    def improve_frontend_prompt(self, recognition: ImageRecognitionResult, framework: str) -> str:
        labels = ", ".join(recognition.labels[:3])
        return f"Create an optimized {framework} UI for: {labels}. Prioritize accessibility, performance, and responsive layout."
