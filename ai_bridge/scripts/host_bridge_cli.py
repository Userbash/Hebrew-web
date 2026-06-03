from __future__ import annotations

import json
import sys

from ai_bridge.core.host_bridge import HostBridge, HostBridgeError
from ai_bridge.core.orchestrator import Orchestrator


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    bridge = HostBridge()

    if not argv or argv[0] in {"-h", "--help"}:
        print("Usage: python -m ai_bridge.scripts.host_bridge_cli <command> [args...]")
        print("Special commands: --init, run-test-suite, run-design-audit, local-llm-status")
        return 1

    if argv[0] == "--init":
        bridge.ensure_whitelist()
        print(f"[OK] Whitelist initialized: {bridge.whitelist_file}")
        return 0

    if argv[0] == "run-test-suite":
        project_root = argv[1] if len(argv) > 1 else "."
        orchestrator = Orchestrator()
        result = orchestrator.run_test_suite(project_root=project_root)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result.get("ok") else 1

    if argv[0] == "run-design-audit":
        url = argv[1] if len(argv) > 1 else None
        output_dir = argv[2] if len(argv) > 2 else "test-results"
        orchestrator = Orchestrator()
        result = orchestrator.run_design_audit(url=url, output_dir=output_dir)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result.get("ok") else 1

    if argv[0] == "local-llm-status":
        orchestrator = Orchestrator()
        payload = {
            "local_llm": orchestrator.local_llm_status(),
            "testing": orchestrator.testing_status(),
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    try:
        result = bridge.execute(argv, check=False)
    except HostBridgeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
