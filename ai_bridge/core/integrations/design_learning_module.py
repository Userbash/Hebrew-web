from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_bridge.core.session_memory import MemoryScope, SessionMemory


@dataclass(slots=True)
class DesignSample:
    project_id: str
    framework: str
    image_labels: list[str]
    user_feedback_score: float
    notes: str = ""


class DesignLearningModule:
    def __init__(self, memory: SessionMemory, namespace: str = "design_learning") -> None:
        self.memory = memory
        self.namespace = namespace

    def add_sample(self, sample: DesignSample) -> None:
        key = f"sample:{sample.project_id}:{sample.framework}"
        self.memory.set(
            MemoryScope.CAPABILITY,
            self.namespace,
            key,
            {
                "framework": sample.framework,
                "labels": sample.image_labels,
                "score": max(0.0, min(1.0, sample.user_feedback_score)),
                "notes": sample.notes,
            },
        )

    def suggest_ui_direction(self, framework: str) -> dict[str, Any]:
        keys = self.memory.list_keys(MemoryScope.CAPABILITY, self.namespace)
        framework_l = framework.strip().lower()
        matched: list[dict[str, Any]] = []
        for key in keys:
            prefix = f"{MemoryScope.CAPABILITY.value}:{self.namespace}:"
            logical_key = key[len(prefix):] if key.startswith(prefix) else key
            value = self.memory.get(MemoryScope.CAPABILITY, self.namespace, logical_key)
            if isinstance(value, dict) and str(value.get("framework", "")).lower() == framework_l:
                matched.append(value)

        if not matched:
            return {
                "framework": framework_l,
                "style": "clean-modern",
                "tokens": ["high-contrast", "clear hierarchy", "micro-interactions"],
                "confidence": 0.4,
            }

        avg = sum(float(x.get("score", 0.0)) for x in matched) / len(matched)
        label_counts: dict[str, int] = {}
        for item in matched:
            for label in item.get("labels", []):
                label_counts[str(label).lower()] = label_counts.get(str(label).lower(), 0) + 1
        top_labels = sorted(label_counts, key=label_counts.get, reverse=True)[:5]
        return {
            "framework": framework_l,
            "style": "data-trained-modern",
            "tokens": top_labels or ["responsive", "accessible", "distinctive"],
            "confidence": round(min(0.95, 0.5 + avg * 0.5), 2),
        }
