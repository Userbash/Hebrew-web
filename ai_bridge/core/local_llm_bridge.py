from __future__ import annotations

import logging
import os
import shlex
import subprocess

import requests
from dataclasses import dataclass, field
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from ai_bridge.core.host_bridge import HostBridge
from ai_bridge.scripts import deploy_local_llm

logger = logging.getLogger("local_llm_bridge")


@dataclass(slots=True)
class LocalLLMBridge:
    container_name: str = "ai-kernel-local"
    ollama_host: str = "0.0.0.0"
    ollama_port: int = 11434
    host_bridge: HostBridge = field(default_factory=HostBridge)

    def __init__(
        self,
        container_name: str | None = None,
        ollama_host: str | None = None,
        ollama_port: int | None = None,
        host_bridge: HostBridge | None = None,
    ) -> None:
        default_container = "ai-kernel-local"
        default_host = "0.0.0.0"
        default_port = 11434
        self.container_name = container_name or os.getenv("AI_BRIDGE_LOCAL_LLM_CONTAINER", default_container)
        self.ollama_host = ollama_host or os.getenv("AI_BRIDGE_LOCAL_LLM_HOST", default_host)
        raw_port = ollama_port if ollama_port is not None else os.getenv("AI_BRIDGE_LOCAL_LLM_PORT", str(default_port))
        try:
            self.ollama_port = int(raw_port)
        except (TypeError, ValueError):
            self.ollama_port = default_port
        self.host_bridge = host_bridge or HostBridge()

    def _run(self, args: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
        try:
            return self.host_bridge.execute(args, check=check)
        except Exception as exc:
            # Fallback for non-whitelisted commands or other bridge errors
            logger.debug("Host bridge execution failed for %s: %s. Falling back to direct execution.", args, exc)
            return subprocess.run(args, capture_output=True, text=True, check=check)

    def container_exists(self) -> bool:
        try:
            result = self._run(["distrobox", "list", "--no-color"])
            return result.returncode == 0 and self.container_name in result.stdout
        except Exception:
            return False

    def is_container_running(self) -> bool:
        try:
            result = self._run(["distrobox", "list", "--no-color"])
            if result.returncode != 0:
                return False
            for line in result.stdout.splitlines():
                if self.container_name in line and "Running" in line:
                    return True
            return False
        except Exception:
            return False

    def is_model_downloaded(self, model_name: str) -> bool:
        try:
            result = self._run(["distrobox", "enter", self.container_name, "--", "ollama", "list"])
            return result.returncode == 0 and model_name in result.stdout
        except Exception:
            return False

    def _host_probe(self) -> dict[str, Any]:
        url = f"http://host.containers.internal:{self.ollama_port}/api/tags"
        try:
            with urlopen(url, timeout=5) as response:
                payload = response.read().decode("utf-8")
                return {"ok": True, "status_code": getattr(response, "status", 200), "body": payload, "url": url}
        except URLError as exc:
            return {"ok": False, "error": str(exc), "url": url}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "url": url}

    def ensure_ready(self, model_name: str) -> bool:
        auto_provision = os.getenv("AI_BRIDGE_LOCAL_LLM_AUTO_PROVISION", "true").strip().lower() in {"1", "true", "yes", "on"}
        if not self.container_exists():
            if not auto_provision:
                logger.warning("Local LLM container '%s' does not exist; skipping autostart.", self.container_name)
                return False
            try:
                deploy_local_llm.CONTAINER_NAME = self.container_name
                deploy_local_llm.MODEL_NAME = model_name
                deploy_local_llm.OLLAMA_HOST = self.ollama_host
                deploy_local_llm.OLLAMA_PORT = str(self.ollama_port)
                deploy_local_llm.ensure_container(self.container_name)
                deploy_local_llm.install_ollama(self.container_name)
                deploy_local_llm.start_service(self.container_name)
            except Exception as exc:
                logger.warning("Failed to auto-provision local LLM container '%s': %s", self.container_name, exc)
                return False

        quoted_model = shlex.quote(model_name)
        boot_cmd = (
            "set -euo pipefail; "
            f"export OLLAMA_HOST={shlex.quote(self.ollama_host)} OLLAMA_ORIGINS='*'; "
            "if ! pgrep -x ollama >/dev/null 2>&1; then nohup ollama serve > /tmp/ollama.log 2>&1 & fi; "
            "sleep 2; "
            f"ollama pull {quoted_model}"
        )
        result = self._run(["distrobox", "enter", self.container_name, "--", "bash", "-lc", boot_cmd])
        if result.returncode != 0:
            logger.warning("Failed to bootstrap local LLM container '%s': %s", self.container_name, (result.stderr or result.stdout).strip())
            return False

        probe = self._host_probe()
        if not probe.get("ok"):
            logger.warning("Local LLM host bridge is not reachable: %s", probe.get("error", "unknown error"))
            return False

        return self.is_model_downloaded(model_name)

    def query(self, prompt: str, model_name: str) -> str:
        url = f"http://host.containers.internal:{self.ollama_port}/api/generate"
        response = requests.post(
            url,
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        if not isinstance(payload, dict):
            raise RuntimeError("invalid local LLM response")
        text = payload.get("response")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("empty local LLM response")
        return text.strip()
