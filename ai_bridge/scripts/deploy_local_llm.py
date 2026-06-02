from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONTAINER_NAME = os.getenv("AI_BRIDGE_LOCAL_LLM_CONTAINER", "ai-kernel-local")
MODEL_NAME = os.getenv("AI_BRIDGE_LOCAL_LLM_MODEL", "qwen2.5:32b-instruct-q4_k_m")
OLLAMA_HOST = os.getenv("AI_BRIDGE_LOCAL_LLM_HOST", "0.0.0.0")
OLLAMA_PORT = os.getenv("AI_BRIDGE_LOCAL_LLM_PORT", "11434")


def run_command(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def distrobox_exists(container_name: str) -> bool:
    result = run_command(["distrobox", "list", "--no-color"], check=False)
    if result.returncode != 0:
        return False
    return container_name in result.stdout


def ensure_container(container_name: str) -> None:
    if distrobox_exists(container_name):
        return
    run_command([
        "distrobox",
        "create",
        "--name",
        container_name,
        "--image",
        "docker.io/library/debian:bookworm",
        "--yes",
        "--nvidia",
        "--additional-flags",
        f"--publish {OLLAMA_PORT}:{OLLAMA_PORT}",
    ])


def install_ollama(container_name: str) -> None:
    install_script = (
        "set -euo pipefail; "
        "export DEBIAN_FRONTEND=noninteractive; "
        "apt-get update; "
        "apt-get install -y curl ca-certificates python3-pip; "
        "curl -fsSL https://ollama.com/install.sh | sh"
    )
    run_command(["distrobox", "enter", container_name, "--", "bash", "-lc", install_script])


def start_service(container_name: str) -> None:
    serve_cmd = (
        f"set -euo pipefail; "
        f"OLLAMA_HOST={OLLAMA_HOST} OLLAMA_ORIGINS='*' nohup ollama serve > /tmp/ollama.log 2>&1 & "
        "sleep 5; "
        f"ollama pull {MODEL_NAME}"
    )
    run_command(["distrobox", "enter", container_name, "--", "bash", "-lc", serve_cmd])


def verify_ready() -> bool:
    probe_url = f"http://127.0.0.1:{OLLAMA_PORT}/api/tags"
    probe = run_command([
        "python3",
        "-c",
        (
            "import json, urllib.request; "
            f"resp = urllib.request.urlopen('{probe_url}', timeout=10); "
            "payload = json.load(resp); "
            "models = payload.get('models', []) if isinstance(payload, dict) else []; "
            f"expected = '{MODEL_NAME}'; "
            "print(expected in {item.get('name', '') for item in models if isinstance(item, dict)})"
        ),
    ], check=False)
    return probe.returncode == 0 and probe.stdout.strip().endswith("True")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Provision a local Ollama distrobox for AI Bridge")
    parser.add_argument("--container", default=CONTAINER_NAME)
    parser.add_argument("--model", default=MODEL_NAME)
    parser.add_argument("--port", default=OLLAMA_PORT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    global CONTAINER_NAME, MODEL_NAME, OLLAMA_PORT
    CONTAINER_NAME = args.container
    MODEL_NAME = args.model
    OLLAMA_PORT = args.port

    ensure_container(CONTAINER_NAME)
    install_ollama(CONTAINER_NAME)
    start_service(CONTAINER_NAME)

    if not verify_ready():
        print(f"ERROR: model {MODEL_NAME} is not reachable on {OLLAMA_PORT}.", file=sys.stderr)
        return 1

    print(f"Deployment complete. Ollama bridge is reachable at http://127.0.0.1:{OLLAMA_PORT}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
