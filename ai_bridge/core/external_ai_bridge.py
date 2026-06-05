from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass

try:
    from tenacity import RetryError, Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter
except Exception:  # pragma: no cover
    RetryError = None  # type: ignore
    Retrying = None  # type: ignore
    retry_if_exception_type = None  # type: ignore
    stop_after_attempt = None  # type: ignore
    wait_exponential_jitter = None  # type: ignore

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
    def resolve_gemini_cli_command() -> list[str] | None:
        env_bin = os.getenv("GEMINI_CLI_BIN", "").strip()
        if env_bin:
            resolved = shutil.which(env_bin) if not os.path.isabs(env_bin) else env_bin
            if resolved and os.access(resolved, os.X_OK):
                return [resolved]

        for candidate in ("gemini", "google-gemini", "gemini-cli"):
            resolved = shutil.which(candidate)
            if resolved:
                return [resolved]

        npx = shutil.which("npx")
        if npx:
            return [npx, "@google/gemini-cli"]
        return None

    @staticmethod
    def _gemini_runtime_env() -> dict[str, str]:
        env = os.environ.copy()
        home_dir = env.get("HOME", "")
        if home_dir:
            local_bin = os.path.join(home_dir, ".local", "bin")
            current_path = env.get("PATH", "")
            if local_bin and local_bin not in current_path.split(os.pathsep):
                env["PATH"] = f"{local_bin}{os.pathsep}{current_path}" if current_path else local_bin
        node_path = shutil.which("node")
        if node_path:
            return env
        npx = shutil.which("npx")
        if npx:
            node_dir = os.path.dirname(npx)
            current_path = env.get("PATH", "")
            if node_dir and node_dir not in current_path.split(os.pathsep):
                env["PATH"] = f"{node_dir}{os.pathsep}{current_path}" if current_path else node_dir
        return env

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
            cmd_prefix = self.resolve_gemini_cli_command()
            if not cmd_prefix:
                return BridgeExecResult(False, "", "gemini_cli_not_found", "gemini-cli", model, attempts, error_type="unknown")

            cmd = [
                *cmd_prefix,
                "--prompt",
                prompt,
                "--model",
                model,
                "--output-format",
                "text",
                "--skip-trust",
            ]

            def _run_once() -> subprocess.CompletedProcess[str]:
                if self.host_bridge is not None:
                    try:
                        res = self.host_bridge.execute(cmd, timeout=timeout_sec, capture_output=True, text=True, check=False)
                        # If command not found on host (exit code 1 from flatpak-spawn or 127 from shell), fallback to local
                        # We also check for 'npx' or command name in stderr if it failed
                        if res.returncode in (1, 127):
                            stderr = (res.stderr or "").lower()
                            # Common error markers for missing binary
                            if any(marker in stderr for marker in ["нет такого файла", "no such file", "not found", "failed to start command"]):
                                return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, env=self._gemini_runtime_env())
                        return res
                    except Exception:
                        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, env=self._gemini_runtime_env())
                return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, env=self._gemini_runtime_env())

            if Retrying is not None:
                try:
                    retry_loop = Retrying(
                        stop=stop_after_attempt(retries),
                        wait=wait_exponential_jitter(initial=1, max=8),
                        retry=retry_if_exception_type((subprocess.TimeoutExpired, RuntimeError)),
                        reraise=True,
                    )
                    for attempt in retry_loop:
                        with attempt:
                            attempts += 1
                            proc = _run_once()
                            if proc.returncode != 0:
                                stderr = (proc.stderr or "").strip()
                                err = stderr or f"non-zero exit code: {proc.returncode}"
                                if self._is_capacity_error(err) or self._is_token_error(err):
                                    raise RuntimeError(err)
                                return BridgeExecResult(False, "", err, "gemini-cli", model, attempts, error_type=self.classify_error(err))
                            output = proc.stdout.strip()
                            self.router.register_usage(task, self._estimate_consumed_tokens(prompt, output))
                            return BridgeExecResult(True, output, "", "gemini-cli", model, attempts, error_type="none")
                except RetryError as exc:
                    last_error = str(exc)
                except subprocess.TimeoutExpired as exc:
                    return BridgeExecResult(False, "", f"timeout: {exc}", "gemini-cli", model, attempts, error_type="sdk_hang")
                except RuntimeError as exc:
                    last_error = str(exc)
                    if model and (self._is_capacity_error(last_error) or self._is_token_error(last_error) or self.classify_error(last_error) in {"quota_exhaustion", "auth_fail"}):
                        self.router.block_model(task, model)
                except Exception as exc:
                    return BridgeExecResult(False, "", f"execution_error: {exc}", "gemini-cli", model, attempts, error_type=self.classify_error(str(exc)))
                continue

            for attempt in range(1, retries + 1):
                attempts += 1
                try:
                    proc = _run_once()
                except subprocess.TimeoutExpired as exc:
                    return BridgeExecResult(False, "", f"timeout: {exc}", "gemini-cli", model, attempts, error_type="sdk_hang")
                except Exception as exc:
                    return BridgeExecResult(False, "", f"execution_error: {exc}", "gemini-cli", model, attempts, error_type=self.classify_error(str(exc)))

                if proc.returncode == 0:
                    output = proc.stdout.strip()
                    self.router.register_usage(task, self._estimate_consumed_tokens(prompt, output))
                    return BridgeExecResult(True, output, "", "gemini-cli", model, attempts, error_type="none")

                stderr = (proc.stderr or "").strip()
                last_error = stderr or f"non-zero exit code: {proc.returncode}"
                classified = self.classify_error(last_error)
                retryable = self._is_capacity_error(last_error) or self._is_token_error(last_error) or classified in {"quota_exhaustion", "auth_fail"}
                if retryable and attempt < retries:
                    time.sleep(self._backoff_sec(attempt))
                    continue
                if retryable:
                    self.router.block_model(task, model)
                    break
                return BridgeExecResult(False, "", last_error, "gemini-cli", model, attempts, error_type=classified)

        return BridgeExecResult(False, "", f"routing_exhausted: {last_error}", "gemini-cli", plan.models[-1], attempts, error_type=self.classify_error(last_error))
