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
    error_type: str = "unknown"


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
        return max(8, (len(prompt) + len(output)) // 4)

    @staticmethod
    def classify_error(raw_error: str) -> str:
        text = (raw_error or "").lower()
        if "resource_exhausted" in text or "quota" in text or "429" in text:
            return "quota_exhaustion"
        if any(marker in text for marker in ["401", "403", "api key", "auth", "unauthorized", "forbidden"]):
            return "auth_fail"
        if any(marker in text for marker in ["connecttimeout", "readtimeout", "timed out", "connection timed out", "tcp"]):
            return "tcp_timeout"
        if any(marker in text for marker in ["deadline exceeded", "request timeout", "504", "gateway timeout", "api timeout"]):
            return "api_timeout"
        if any(marker in text for marker in ["hang", "stuck", "did not finish", "no response"]):
            return "sdk_hang"
        return "unknown"

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
                    return BridgeExecResult(False, "", f"timeout: {last_error}", "gemini-cli", model, attempts, error_type="sdk_hang")
                except Exception as exc:
                    last_error = str(exc)
                    return BridgeExecResult(False, "", f"execution_error: {last_error}", "gemini-cli", model, attempts, error_type=self.classify_error(last_error))

                if proc.returncode == 0:
                    output = proc.stdout.strip()
                    self.router.register_usage(task, self._estimate_consumed_tokens(prompt, output))
                    return BridgeExecResult(True, output, "", "gemini-cli", model, attempts, error_type="none")

                stderr = (proc.stderr or "").strip()
                last_error = stderr or f"non-zero exit code: {proc.returncode}"
                error_type = self.classify_error(last_error)

                if (self._is_capacity_error(last_error) or self._is_token_error(last_error)) and attempt < retries:
                    time.sleep(self._backoff_sec(attempt))
                    continue

                if self._is_capacity_error(last_error) or self._is_token_error(last_error):
                    break

                return BridgeExecResult(False, "", last_error, "gemini-cli", model, attempts, error_type=error_type)

        return BridgeExecResult(False, "", f"routing_exhausted: {last_error}", "gemini-cli", plan.models[-1], attempts, error_type=self.classify_error(last_error))
