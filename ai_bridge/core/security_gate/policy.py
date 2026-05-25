from __future__ import annotations

import os
from pathlib import Path

from .authz import PreDeployAuthorization
from .dependency_audit import DependencyAuditCheck
from .external_scanners import ExternalScannersCheck
from .models import SecurityGateReport
from .static_analysis import StaticSecurityCheck


class SecurityGate:
    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.authz = PreDeployAuthorization(self.repo_root)
        self.dependency = DependencyAuditCheck(self.repo_root)
        self.static = StaticSecurityCheck(self.repo_root)
        self.external = ExternalScannersCheck(self.repo_root, require_scanners=os.getenv("AI_BRIDGE_REQUIRE_EXTERNAL_SCANNERS", "false").lower() in {"1","true","yes","on"})

    def run(self, env: dict[str, str] | None = None) -> SecurityGateReport:
        env = env or dict(os.environ)
        reports = [
            self.authz.run(env),
            self.dependency.run(),
            self.static.run(),
        ]

        if env.get("AI_BRIDGE_ENABLE_EXTERNAL_SCANNERS", "true").lower() in {"1", "true", "yes", "on"}:
            reports.append(self.external.run())
        allowed = all(report.allowed for report in reports)
        return SecurityGateReport(allowed=allowed, reports=reports)
