from __future__ import annotations

import struct
import zlib
from pathlib import Path

from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.core.vision_design_audit_module import VisionDesignAuditModule


def _write_png(path: Path, width: int = 400, height: int = 300) -> None:
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            if 20 <= x <= 180 and 20 <= y <= 90:
                row.extend([30, 30, 30])
            elif 220 <= x <= 360 and 40 <= y <= 120:
                row.extend([20, 20, 20])
            elif 40 <= x <= 150 and 180 <= y <= 260:
                row.extend([50, 50, 50])
            else:
                row.extend([255, 255, 255])
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
    png.extend(chunk(b"IDAT", raw))
    png.extend(chunk(b"IEND", b""))
    path.write_bytes(bytes(png))


def test_analyze_screenshot_returns_findings(tmp_path):
    image_path = tmp_path / "audit.png"
    _write_png(image_path)

    module = VisionDesignAuditModule()
    report = module.analyze_screenshot(image_path)

    assert report["ok"] is True
    assert report["findings"]
    assert report["segments"]["horizontal"] or report["segments"]["vertical"]


def test_design_method_builds_repair_plan(tmp_path):
    image_path = tmp_path / "audit.png"
    _write_png(image_path)

    module = VisionDesignAuditModule()
    report = module.analyze_screenshot(image_path)
    plan = module.develop_design_method(report)

    assert plan["workflow"]
    assert plan["repair_plan"]
    assert "issue_count" in plan["summary"]


def test_orchestrator_exposes_vision_design_audit():
    orchestrator = Orchestrator()
    module = orchestrator.get_module("vision_design_audit")
    assert isinstance(module, VisionDesignAuditModule)
