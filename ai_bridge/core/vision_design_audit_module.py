from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .kernel_protocol import KernelAPI, KernelModule


@dataclass(slots=True)
class VisionFinding:
    severity: str
    category: str
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "evidence": self.evidence,
        }


class VisionDesignAuditModule(KernelModule):
    name = "vision_design_audit"

    def __init__(self) -> None:
        self._api: KernelAPI | None = None
        self._last_report: dict[str, Any] = {}

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        api.log("info", "[VISION] vision_design_audit module loaded")

    def on_unload(self) -> None:
        self._api = None

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        return None

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        return None

    def _capture_with_playwright(self, url: str, output_path: Path) -> dict[str, Any]:
        script = f"""
const {{ chromium }} = require('playwright');
(async() => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage({{ viewport: {{ width: 1440, height: 2200 }}, deviceScaleFactor: 1 }});
  await page.goto({json.dumps(url)}, {{ waitUntil: 'networkidle' }});
  await page.screenshot({{ path: {json.dumps(str(output_path))}, fullPage: true }});
  await browser.close();
}})().catch(err => {{ console.error(err); process.exit(1); }});
"""
        proc = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            cwd=Path(os.getenv("AI_BRIDGE_PROJECT_ROOT", ".")).resolve(),
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "output_path": str(output_path),
        }

    def capture_admin_panel(self, url: str | None = None, output_dir: str | Path = "test-results") -> dict[str, Any]:
        target = url or os.getenv("AI_BRIDGE_ADMIN_AUDIT_URL", "http://127.0.0.1:8081/admin")
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        shot = out_dir / "vision_admin_audit.png"
        result = self._capture_with_playwright(target, shot)
        self._last_report = {"capture": result, "url": target, "screenshot": str(shot)}
        return self._last_report

    @staticmethod
    def _decode_png(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
        raw = path.read_bytes()
        signature = b"\x89PNG\r\n\x1a\n"
        if not raw.startswith(signature):
            raise ValueError("unsupported image format; expected PNG")
        pos = len(signature)
        width = height = None
        color_type = None
        idat = bytearray()
        while pos < len(raw):
            length = struct.unpack(">I", raw[pos:pos + 4])[0]
            pos += 4
            chunk_type = raw[pos:pos + 4]
            pos += 4
            chunk_data = raw[pos:pos + length]
            pos += length + 4
            if chunk_type == b"IHDR":
                width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", chunk_data)
                if bit_depth != 8 or compression != 0 or filter_method != 0 or interlace != 0:
                    raise ValueError("unsupported PNG encoding")
            elif chunk_type == b"IDAT":
                idat.extend(chunk_data)
            elif chunk_type == b"IEND":
                break
        if width is None or height is None or color_type is None:
            raise ValueError("invalid PNG")
        data = zlib.decompress(bytes(idat))
        channels = 4 if color_type == 6 else 3 if color_type == 2 else None
        if channels is None:
            raise ValueError("unsupported PNG color type")
        stride = width * channels
        pixels: list[tuple[int, int, int]] = []
        offset = 0
        prev_row = bytearray(stride)

        def paeth(a: int, b: int, c: int) -> int:
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                return a
            if pb <= pc:
                return b
            return c

        for _y in range(height):
            filter_type = data[offset]
            offset += 1
            row = bytearray(data[offset:offset + stride])
            offset += stride
            if filter_type == 1:
                for i in range(stride):
                    left = row[i - channels] if i >= channels else 0
                    row[i] = (row[i] + left) & 0xFF
            elif filter_type == 2:
                for i in range(stride):
                    row[i] = (row[i] + prev_row[i]) & 0xFF
            elif filter_type == 3:
                for i in range(stride):
                    left = row[i - channels] if i >= channels else 0
                    up = prev_row[i]
                    row[i] = (row[i] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                for i in range(stride):
                    left = row[i - channels] if i >= channels else 0
                    up = prev_row[i]
                    up_left = prev_row[i - channels] if i >= channels else 0
                    row[i] = (row[i] + paeth(left, up, up_left)) & 0xFF
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter {filter_type}")
            prev_row = row[:]
            for x in range(0, stride, channels):
                pixels.append((row[x], row[x + 1], row[x + 2]))
        return width, height, pixels

    def _load_rgb(self, path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
        try:
            from PIL import Image  # type: ignore
        except Exception:
            return self._decode_png(path)
        img = Image.open(path).convert("RGB")
        width, height = img.size
        return width, height, list(img.getdata())

    def analyze_screenshot(self, image_path: str | Path) -> dict[str, Any]:
        path = Path(image_path)
        try:
            width, height, data = self._load_rgb(path)
        except Exception as exc:
            return {"ok": False, "error": str(exc), "findings": []}

        rows = []
        cols = []
        for y in range(height):
            dark = 0
            for x in range(width):
                r, g, b = data[y * width + x]
                if (r + g + b) / 3 < 230:
                    dark += 1
            rows.append(dark / max(1, width))
        for x in range(width):
            dark = 0
            for y in range(height):
                r, g, b = data[y * width + x]
                if (r + g + b) / 3 < 230:
                    dark += 1
            cols.append(dark / max(1, height))

        def top_segments(values: list[float], threshold: float = 0.22, min_len: int = 6) -> list[tuple[int, int, float]]:
            segments: list[tuple[int, int, float]] = []
            start: int | None = None
            for idx, value in enumerate(values):
                if value >= threshold and start is None:
                    start = idx
                elif value < threshold and start is not None:
                    if idx - start >= min_len:
                        avg = sum(values[start:idx]) / (idx - start)
                        segments.append((start, idx - 1, avg))
                    start = None
            if start is not None and len(values) - start >= min_len:
                avg = sum(values[start:]) / (len(values) - start)
                segments.append((start, len(values) - 1, avg))
            return segments

        horizontal = top_segments(rows)
        vertical = top_segments(cols)

        left_dark = sum(cols[: width // 2])
        right_dark = sum(cols[width // 2 :])
        top_dark = sum(rows[: height // 2])
        bottom_dark = sum(rows[height // 2 :])
        asym_x = abs(left_dark - right_dark) / max(left_dark + right_dark, 1e-6)
        asym_y = abs(top_dark - bottom_dark) / max(top_dark + bottom_dark, 1e-6)

        findings: list[VisionFinding] = []
        if asym_x > 0.18:
            findings.append(VisionFinding("medium", "alignment", "Content density is horizontally unbalanced", {"asymmetry": round(asym_x, 3)}))
        if asym_y > 0.18:
            findings.append(VisionFinding("medium", "spacing", "Content density is vertically unbalanced", {"asymmetry": round(asym_y, 3)}))
        if len(horizontal) > 20:
            findings.append(VisionFinding("high", "layout", "Too many dense horizontal bands suggest stacked broken blocks", {"bands": len(horizontal)}))
        if len(vertical) > 20:
            findings.append(VisionFinding("high", "layout", "Too many dense vertical bands suggest fragmented columns", {"bands": len(vertical)}))
        if not horizontal and not vertical:
            findings.append(VisionFinding("medium", "visibility", "Low structural contrast makes layout segmentation unclear", {}))

        report = {
            "ok": True,
            "image": str(path),
            "size": {"width": width, "height": height},
            "density": {
                "left_dark": round(left_dark, 3),
                "right_dark": round(right_dark, 3),
                "top_dark": round(top_dark, 3),
                "bottom_dark": round(bottom_dark, 3),
            },
            "segments": {
                "horizontal": horizontal[:40],
                "vertical": vertical[:40],
            },
            "findings": [f.as_dict() for f in findings],
        }
        self._last_report = report
        return report

    def develop_design_method(self, audit_report: dict[str, Any]) -> dict[str, Any]:
        findings = audit_report.get("findings", []) if isinstance(audit_report, dict) else []
        actions: list[dict[str, Any]] = []
        for finding in findings:
            category = str(finding.get("category", "unknown"))
            if category == "alignment":
                actions.append({"step": "normalize grid alignment", "priority": "high", "details": "re-center the main content columns and remove uneven offsets."})
            elif category == "spacing":
                actions.append({"step": "rebalance vertical rhythm", "priority": "high", "details": "standardize gaps, section heights, and sticky areas."})
            elif category == "layout":
                actions.append({"step": "collapse broken blocks", "priority": "critical", "details": "merge fragmented cards into a coherent hierarchy and restore block boundaries."})
            else:
                actions.append({"step": "manual review", "priority": "medium", "details": "inspect the screen for visual noise and accessibility regression."})

        if not actions:
            actions.append({"step": "design accepted", "priority": "low", "details": "No major layout defects detected."})

        return {
            "workflow": [
                "capture admin panel screenshot",
                "analyze image structure and alignment",
                "prioritize defects by severity",
                "generate design repair plan",
                "apply frontend layout corrections",
                "re-run visual audit",
            ],
            "repair_plan": actions,
            "summary": {
                "issue_count": len(findings),
                "highest_risk": max((str(item.get("severity", "low")) for item in findings), default="low"),
            },
        }

    def run_audit(self, url: str | None = None, output_dir: str | Path = "test-results") -> dict[str, Any]:
        capture = self.capture_admin_panel(url=url, output_dir=output_dir)
        if not capture.get("capture", {}).get("ok"):
            self._last_report = {"ok": False, "capture": capture}
            return self._last_report
        analysis = self.analyze_screenshot(capture["screenshot"])
        design_method = self.develop_design_method(analysis)
        self._last_report = {
            "ok": analysis.get("ok", False),
            "capture": capture,
            "analysis": analysis,
            "design_method": design_method,
        }
        return self._last_report

    def finalize(self) -> dict[str, Any]:
        return self._last_report
