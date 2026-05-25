from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .models import SecurityCheckReport, SecurityIssue


SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


class ExternalScannersCheck:
    def __init__(self, repo_root: Path, require_scanners: bool = False) -> None:
        self.repo_root = repo_root
        self.require_scanners = require_scanners

    def _tool_exists(self, tool: str) -> bool:
        return shutil.which(tool) is not None

    def _run(self, cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)

    def _severity_from_text(self, text: str) -> str | None:
        m = re.search(r"\b(CRITICAL|HIGH|MEDIUM|LOW|INFO)\b", text, flags=re.IGNORECASE)
        if not m:
            return None
        return m.group(1).lower()

    def _parse_json_findings(self, payload: str, tool: str) -> list[SecurityIssue]:
        issues: list[SecurityIssue] = []
        try:
            data = json.loads(payload)
        except Exception:
            return issues

        if tool == "trivy":
            for item in data.get("Results", []) or []:
                target = item.get("Target")
                for vuln in item.get("Vulnerabilities", []) or []:
                    sev = str(vuln.get("Severity", "medium")).lower()
                    issues.append(SecurityIssue(
                        category="cve",
                        severity=sev,
                        message=f"trivy:{vuln.get('VulnerabilityID', 'unknown')} {vuln.get('Title', '')}".strip(),
                        location=str(target) if target else None,
                        recommendation="Update affected package or base image",
                    ))

        if tool == "osv-scanner":
            for result in data.get("results", []) or []:
                source = (result.get("source") or {}).get("path")
                for pkg in result.get("packages", []) or []:
                    for vuln in pkg.get("vulnerabilities", []) or []:
                        sev = "medium"
                        score = (vuln.get("database_specific") or {}).get("severity", "")
                        if isinstance(score, str) and score:
                            sev = score.lower()
                        issues.append(SecurityIssue(
                            category="cve",
                            severity=sev if sev in SEVERITY_ORDER else "medium",
                            message=f"osv:{vuln.get('id', 'unknown')}",
                            location=str(source) if source else None,
                            recommendation="Upgrade vulnerable dependency",
                        ))

        if tool == "semgrep":
            for result in data.get("results", []) or []:
                extra = result.get("extra", {})
                sev = str(extra.get("severity", "medium")).lower()
                issues.append(SecurityIssue(
                    category="sast",
                    severity=sev if sev in SEVERITY_ORDER else "medium",
                    message=f"semgrep:{result.get('check_id', 'rule')} {extra.get('message', '')}".strip(),
                    location=str(result.get("path")) if result.get("path") else None,
                    recommendation="Fix code issue reported by semgrep rule",
                ))

        if tool == "gitleaks":
            findings = data if isinstance(data, list) else data.get("findings", [])
            for item in findings or []:
                issues.append(SecurityIssue(
                    category="secret",
                    severity="critical",
                    message=f"gitleaks:{item.get('RuleID', 'secret')} potential secret leak",
                    location=str(item.get("File")) if item.get("File") else None,
                    recommendation="Remove secret, rotate credentials, add secret scanning baseline",
                ))

        return issues

    def _missing_tool_issue(self, tool: str) -> SecurityIssue:
        return SecurityIssue(
            category="scanner",
            severity="medium" if not self.require_scanners else "high",
            message=f"external scanner not installed: {tool}",
            recommendation=f"Install {tool} or disable strict requirement",
        )

    def run(self) -> SecurityCheckReport:
        issues: list[SecurityIssue] = []

        # Dependabot check is config-based in repo (not a CLI scanner)
        dependabot_file = self.repo_root / ".github" / "dependabot.yml"
        if not dependabot_file.exists():
            issues.append(SecurityIssue(
                category="supply-chain",
                severity="medium",
                message="Dependabot config not found (.github/dependabot.yml)",
                recommendation="Add Dependabot config for automated dependency updates",
            ))

        scanners: list[tuple[str, list[str]]] = [
            ("trivy", ["trivy", "fs", "--format", "json", "."]),
            ("osv-scanner", ["osv-scanner", "scan", "--json", "."]),
            ("semgrep", ["semgrep", "scan", "--config", "auto", "--json", "."]),
            ("gitleaks", ["gitleaks", "detect", "--source", ".", "--report-format", "json", "--report-path", "-"]),
        ]

        for tool, cmd in scanners:
            if not self._tool_exists(tool):
                if self.require_scanners:
                    issues.append(self._missing_tool_issue(tool))
                continue

            result = self._run(cmd)
            if result.stdout.strip():
                issues.extend(self._parse_json_findings(result.stdout, tool))

            if result.returncode != 0 and tool in {"trivy", "osv-scanner", "semgrep", "gitleaks"}:
                sev = self._severity_from_text(result.stderr or "") or "medium"
                # Do not duplicate if structured findings already created
                if not result.stdout.strip():
                    issues.append(SecurityIssue(
                        category="scanner",
                        severity=sev if sev in SEVERITY_ORDER else "medium",
                        message=f"{tool} returned non-zero exit code {result.returncode}",
                        recommendation="Inspect scanner output and fix findings",
                    ))

        highest = max((SEVERITY_ORDER.get(item.severity, 0) for item in issues), default=0)
        allowed = highest < SEVERITY_ORDER["high"]
        return SecurityCheckReport(name="external_scanners", allowed=allowed, issues=issues)
