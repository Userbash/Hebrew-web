from __future__ import annotations

import sys

from ai_bridge.core.host_bridge import HostBridge, HostBridgeError


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    bridge = HostBridge()

    if not argv or argv[0] in {"-h", "--help"}:
        print("Usage: python -m ai_bridge.scripts.host_bridge_cli <command> [args...]")
        return 1

    if argv[0] == "--init":
        bridge.ensure_whitelist()
        print(f"[OK] Whitelist initialized: {bridge.whitelist_file}")
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
