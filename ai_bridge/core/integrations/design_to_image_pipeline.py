from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


_DEFAULT_NEGATIVE_PROMPT = (
    "blurry, low quality, distorted anatomy, broken perspective, watermark, noisy background, "
    "extra limbs, unreadable text, nsfw, gore"
)


@dataclass(slots=True)
class DesignToImagePlan:
    prompt: str
    negative_prompt: str
    model_hint: str | None
    width: int
    height: int
    steps: int
    guidance_scale: float
    output_name: str
    metadata: dict[str, Any]


class DesignToImagePipeline:
    def __init__(self, default_negative_prompt: str | None = None) -> None:
        self.default_negative_prompt = (default_negative_prompt or _DEFAULT_NEGATIVE_PROMPT).strip()

    @staticmethod
    def _clean_text(value: Any) -> str:
        text = str(value or "")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _slug(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug[:64] or "design-concept"

    @staticmethod
    def _listify(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        text = str(value).strip()
        if not text:
            return []
        return [chunk.strip() for chunk in re.split(r"[,;/\n]+", text) if chunk.strip()]

    @staticmethod
    def _canvas_for_layout(layout: str, target_surface: str) -> tuple[int, int]:
        layout_lower = layout.lower()
        surface_lower = target_surface.lower()
        if "mobile" in surface_lower or "phone" in surface_lower:
            return 832, 1216
        if "dashboard" in layout_lower or "admin" in layout_lower or "analytics" in layout_lower:
            return 1344, 768
        if "landing" in layout_lower or "hero" in layout_lower:
            return 1216, 832
        if "poster" in surface_lower:
            return 1024, 1536
        return 1024, 1024

    @staticmethod
    def _model_hint(vibe: str, style: str, brief: str) -> str | None:
        joined = " ".join([vibe, style, brief]).lower()
        if any(token in joined for token in ("anime", "manga", "cel shaded", "cartoon")):
            return "anime"
        if any(token in joined for token in ("photo", "photoreal", "realistic", "cinematic")):
            return "photo"
        if any(token in joined for token in ("wireframe", "dashboard", "ui", "ux", "product")):
            return "ui"
        if any(token in joined for token in ("illustration", "concept art", "vector")):
            return "illustration"
        return None

    def normalize_design_input(self, design_input: Any) -> dict[str, Any]:
        if isinstance(design_input, dict):
            brief = self._clean_text(
                design_input.get("brief")
                or design_input.get("description")
                or design_input.get("prompt")
                or design_input.get("objective")
                or design_input.get("summary")
            )
            layout = self._clean_text(design_input.get("layout") or design_input.get("structure") or "interface")
            vibe = self._clean_text(design_input.get("vibe") or design_input.get("style") or "modern")
            color = self._clean_text(design_input.get("primary_color") or design_input.get("accent_color") or "")
            components = self._listify(design_input.get("components"))
            audience = self._clean_text(design_input.get("audience") or design_input.get("persona") or "")
            surface = self._clean_text(design_input.get("target_surface") or design_input.get("surface") or "web")
            output_name = self._clean_text(design_input.get("output_name") or "")
            return {
                "brief": brief,
                "layout": layout,
                "vibe": vibe,
                "color": color,
                "components": components,
                "audience": audience,
                "target_surface": surface,
                "output_name": output_name,
            }

        brief = self._clean_text(design_input)
        return {
            "brief": brief,
            "layout": "interface",
            "vibe": "modern",
            "color": "",
            "components": [],
            "audience": "",
            "target_surface": "web",
            "output_name": "",
        }

    def build_plan(self, design_input: Any, overrides: dict[str, Any] | None = None) -> DesignToImagePlan:
        data = self.normalize_design_input(design_input)
        extra = overrides or {}

        brief = self._clean_text(extra.get("brief") or data["brief"] or "product interface concept")
        layout = self._clean_text(extra.get("layout") or data["layout"] or "interface")
        vibe = self._clean_text(extra.get("vibe") or data["vibe"] or "modern")
        color = self._clean_text(extra.get("primary_color") or data["color"])
        audience = self._clean_text(extra.get("audience") or data["audience"])
        target_surface = self._clean_text(extra.get("target_surface") or data["target_surface"] or "web")
        components = self._listify(extra.get("components") or data["components"])
        width, height = self._canvas_for_layout(layout, target_surface)

        if isinstance(extra.get("width"), int) and extra["width"] > 0:
            width = extra["width"]
        if isinstance(extra.get("height"), int) and extra["height"] > 0:
            height = extra["height"]

        detail_tags = [
            "high fidelity product mockup",
            f"{vibe} visual language",
            f"{layout} composition",
            f"for {target_surface}",
        ]
        if color:
            detail_tags.append(f"dominant accent color {color}")
        if components:
            detail_tags.append("key elements: " + ", ".join(components[:8]))
        if audience:
            detail_tags.append(f"designed for {audience}")

        prompt_parts = [brief, *detail_tags, "clean hierarchy", "balanced spacing", "studio lighting", "high detail"]
        prompt = ", ".join(part for part in prompt_parts if part)
        negative_prompt = self._clean_text(extra.get("negative_prompt") or self.default_negative_prompt)
        model_hint = self._model_hint(vibe, layout, brief)

        steps = int(extra.get("steps") or 30)
        guidance_scale = float(extra.get("guidance_scale") or 7.0)
        output_base = self._clean_text(extra.get("output_name") or data["output_name"] or brief)
        output_name = f"{self._slug(output_base)}.png"

        return DesignToImagePlan(
            prompt=prompt,
            negative_prompt=negative_prompt,
            model_hint=model_hint,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=guidance_scale,
            output_name=output_name,
            metadata={
                "brief": brief,
                "layout": layout,
                "vibe": vibe,
                "components": components,
                "target_surface": target_surface,
                "primary_color": color,
                "audience": audience,
            },
        )
