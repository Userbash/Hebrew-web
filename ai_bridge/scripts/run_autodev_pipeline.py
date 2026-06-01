from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ai_bridge.core.orchestrator import Orchestrator


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run integrated AI Bridge autodev pipeline")
    p.add_argument("--spec", required=True, help="Project specification text")
    p.add_argument("--project-root", default=".", help="Project root path to run lint/tests")
    p.add_argument("--figma", action="store_true", help="Enable figma mode if available")
    return p


def main() -> None:
    args = build_parser().parse_args()
    os.environ.setdefault("AI_BRIDGE_API_ENABLED", "0")
    os.environ.setdefault("AI_BRIDGE_AUTODEV_HEADLESS", "1")
    orchestrator = Orchestrator()
    result = orchestrator.run_autodev_pipeline(
        specs=args.spec,
        project_root=str(Path(args.project_root).resolve()),
        figma_api_available=args.figma,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
