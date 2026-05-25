from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass

from ai_bridge.core.gemini_runtime_router import GeminiRuntimeRouter
from ai_bridge.core.host_bridge import HostBridge
from ai_bridge.core.models import Task


@dataclass(slots=True)
class BridgeExecResult:
    ok: bool
    output: str
    error: str
    provider: str
    model: str
    attempts: int


class ExternalAIBridge:
    def __init__(self, host_bridge: HostBridge | None = None) -> None:
        self.host_bridge = host_bridge
        self.router = GeminiRuntimeRouter()

    @staticmethod
    def _retries() -> int:
        raw = os.getenv("EXTERNAL_AI_RETRIES", "3").strip()
        try:
            return max(1, int(raw))
        except ValueError:
            return 3

    @staticmethod
    def _backoff_sec(attempt: int) -> float:
        return min(8.0, 1.25 * attempt)

    @staticmethod
    def _is_capacity_error(stderr: str) -> bool:
        text = (stderr or "").lower()
        return "resource_exhausted" in text or "model_capacity_exhausted" in text or "status 429" in text

    @staticmethod
    def _is_token_error(stderr: str) -> bool:
        text = (stderr or "").lower()
        token_markers = ["token", "context length", "max output tokens", "quota exceeded"]
        return any(marker in text for marker in token_markers)

    @staticmethod
    def _estimate_consumed_tokens(prompt: str, output: str) -> int:
        # Approximation for budget tracking in CLI mode.
        return max(8, (len(prompt) + len(output)) // 4)

    def run_gemini_cli(self, task: Task, prompt: str, timeout_sec: int = 120) -> BridgeExecResult:
        retries = self._retries()
        plan = self.router.build_plan(task, prompt)
        attempts = 0
        last_error = ""

        for model in plan.models:
            for attempt in range(1, retries + 1):
                attempts += 1
                cmd = [
                    "npx",
                    "@google/gemini-cli",
                    "--prompt",
                    prompt,
                    "--model",
                    model,
                    "--output-format",
                    "text",
                ]
                try:
                    if self.host_bridge is not None:
                        proc = self.host_bridge.execute(cmd, timeout=timeout_sec, capture_output=True, text=True, check=False)
                    else:
                        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
                except subprocess.TimeoutExpired as exc:
                    last_error = str(exc)
                    return BridgeExecResult(False, "", f"timeout: {last_error}", "gemini-cli", model, attempts)
                except Exception as exc:  # pragma: no cover - OS edge
                    last_error = str(exc)
                    return BridgeExecResult(False, "", f"execution_error: {last_error}", "gemini-cli", model, attempts)

                if proc.returncode == 0:
                    output = proc.stdout.strip()
                    self.router.register_usage(task, self._estimate_consumed_tokens(prompt, output))
                    return BridgeExecResult(True, output, "", "gemini-cli", model, attempts)

                stderr = (proc.stderr or "").strip()
                last_error = stderr or f"non-zero exit code: {proc.returncode}"

                if (self._is_capacity_error(last_error) or self._is_token_error(last_error)) and attempt < retries:
                    time.sleep(self._backoff_sec(attempt))
                    continue

                # On hard capacity/token exhaustion, try next model in plan.
                if self._is_capacity_error(last_error) or self._is_token_error(last_error):
                    break

                return BridgeExecResult(False, "", last_error, "gemini-cli", model, attempts)

        return BridgeExecResult(False, "", f"routing_exhausted: {last_error}", "gemini-cli", plan.models[-1], attempts)
