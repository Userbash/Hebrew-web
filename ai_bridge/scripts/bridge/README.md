# AI Host Bridge

Bridge logic is implemented in the orchestrator core module:
- `ai_bridge/core/host_bridge.py`
- `ai_bridge/scripts/host_bridge_cli.py`

Shell entrypoint for compatibility:
- `scripts/bridge/exec.sh`

Usage:
```bash
bash scripts/bridge/exec.sh --init
bash scripts/bridge/exec.sh podman ps
bash scripts/bridge/exec.sh podman compose -f docker-compose.yml up -d
```

Notes:
- The bridge validates commands against `scripts/bridge/whitelist.txt`.
- For `podman compose`, the bridge auto-translates to available host provider:
  `docker compose` -> `docker-compose` -> `podman-compose`.
