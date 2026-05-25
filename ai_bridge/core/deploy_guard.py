from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DeployGuardResult:
    allowed: bool
    reasons: list[str]


class DeployGuard:
    """Local-only deployment guard.

    Deployment is allowed only on local systems and blocked in CI/GitHub Actions.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()

    def evaluate(self, env: dict[str, str] | None = None) -> DeployGuardResult:
        env = env or dict(os.environ)
        reasons: list[str] = []

        if env.get("GITHUB_ACTIONS", "").strip().lower() == "true":
            reasons.append("blocked: GITHUB_ACTIONS=true (deployment is local-only)")

        if env.get("GITHUB_WORKFLOW"):
            reasons.append("blocked: running inside GitHub workflow context")

        ci_flag = env.get("CI", "").strip().lower()
        if ci_flag in {"1", "true", "yes"}:
            reasons.append("blocked: CI=true (deployment is local-only)")

        if platform.system().lower() not in {"linux", "darwin"}:
            reasons.append(f"blocked: unsupported local platform '{platform.system()}'")

        required_paths = [
            self.repo_root / "docker-compose.yml",
            self.repo_root / "scripts" / "build_abstracted.sh",
            self.repo_root / "scripts" / "start_manual.sh",
        ]
        for path in required_paths:
            if not path.exists():
                reasons.append(f"blocked: required file not found: {path}")

        return DeployGuardResult(allowed=not reasons, reasons=reasons)

    def assert_allowed(self, env: dict[str, str] | None = None) -> None:
        result = self.evaluate(env)
        if not result.allowed:
            raise RuntimeError("Deployment guard rejected execution:\n- " + "\n- ".join(result.reasons))
