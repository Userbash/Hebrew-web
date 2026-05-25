from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .models import SecurityCheckReport, SecurityIssue


class DependencyAuditCheck:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def _run_npm_audit(self, workdir: Path) -> tuple[int, dict]:
        proc = subprocess.run(
            ["npm", "audit", "--audit-level=low", "--json"],
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        payload = {}
        if proc.stdout.strip():
            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError:
                payload = {}
        return proc.returncode, payload

    def run(self) -> SecurityCheckReport:
        issues: list[SecurityIssue] = []
        targets = [
            self.repo_root / "backend",
            self.repo_root / "frontend-react",
        ]

        for target in targets:
            if not target.exists():
                continue
            _, payload = self._run_npm_audit(target)
            meta = payload.get("metadata", {}).get("vulnerabilities", {})
            total = int(meta.get("total", 0))
            high = int(meta.get("high", 0))
            critical = int(meta.get("critical", 0))

            if total > 0:
                issues.append(SecurityIssue(
                    category="dependency",
                    severity="high" if (high > 0 or critical > 0) else "medium",
                    message=f"{target.name}: vulnerabilities found total={total}, high={high}, critical={critical}",
                    location=str(target),
                    recommendation="Upgrade vulnerable packages and regenerate lockfile",
                ))

            vulnerabilities = payload.get("vulnerabilities", {})
            for name, details in vulnerabilities.items():
                sev = str(details.get("severity", "low"))
                via = details.get("via", [])
                title = None
                if isinstance(via, list):
                    for item in via:
                        if isinstance(item, dict) and item.get("title"):
                            title = item.get("title")
                            break
                issues.append(SecurityIssue(
                    category="cve",
                    severity=sev,
                    message=f"{target.name}:{name} {title or 'vulnerability detected'}",
                    location=str(target / "package.json"),
                    recommendation="Review advisory and update dependency",
                ))

        allowed = not any(issue.severity in {"high", "critical"} for issue in issues)
        return SecurityCheckReport(name="dependency_audit", allowed=allowed, issues=issues)
