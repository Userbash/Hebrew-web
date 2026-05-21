from __future__ import annotations

import argparse

from ai_bridge.core.agent_registry import AgentRegistry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("id")
    parser.add_argument("type")
    parser.add_argument("endpoint")
    parser.add_argument("capabilities", nargs="+")
    args = parser.parse_args()
    registry = AgentRegistry()
    agent = registry.register(args.id, args.type, args.endpoint, args.capabilities)
    print({"id": agent.id, "type": agent.type.value, "capabilities": agent.capabilities})


if __name__ == "__main__":
    main()
