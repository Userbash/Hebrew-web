from __future__ import annotations

import re
from pathlib import Path

from .models import SecurityCheckReport, SecurityIssue

SQLI_PATTERNS = [
    re.compile(r"query\(\s*f['\"]", re.IGNORECASE),
    re.compile(r"query\(\s*`[^`]{0,500}(?<!\$)\$\{", re.IGNORECASE),
    re.compile(r"SELECT\s+.+\+", re.IGNORECASE),
]

RCE_PATTERNS = [
    re.compile(r"eval\(", re.IGNORECASE),
    re.compile(r"new\s+Function\(", re.IGNORECASE),
    re.compile(r"child_process\.(exec|spawn)\(", re.IGNORECASE),
]

WEAK_ENV_PATTERNS = [
    re.compile(r"JWT_SECRET\s*=\s*['\"]?dev_", re.IGNORECASE),
    re.compile(r"PASSWORD\s*=\s*['\"]?(123|password)", re.IGNORECASE),
]




def _load_reviewed_sql_files(repo_root: Path) -> set[str]:
    reviewed = repo_root / ".ai_bridge" / "security-reviewed-sql.txt"
    if not reviewed.exists():
        return set()
    items = {line.strip().replace('\\', '/') for line in reviewed.read_text(encoding='utf-8').splitlines() if line.strip() and not line.strip().startswith('#')}
    return items

class StaticSecurityCheck:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def _scan_file(self, path: Path) -> list[SecurityIssue]:
        issues: list[SecurityIssue] = []
        reviewed_sql = _load_reviewed_sql_files(self.repo_root)
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return issues

        rel_path = str(path.relative_to(self.repo_root)).replace('\\', '/') if path.is_absolute() else str(path).replace('\\', '/')

        for pattern in SQLI_PATTERNS:
            if pattern.search(content):
                base_severity = "medium" if r"(?<!\$)\$\{" in pattern.pattern else "high"
                if base_severity == "medium" and rel_path in reviewed_sql:
                    continue
                issues.append(SecurityIssue(
                    category="sqli",
                    severity=base_severity,
                    message=f"Potential SQL injection pattern matched: {pattern.pattern}",
                    location=str(path),
                    recommendation="Use parameterized queries only and avoid dynamic SQL template construction",
                ))

        for pattern in RCE_PATTERNS:
            if pattern.search(content):
                issues.append(SecurityIssue(
                    category="rce",
                    severity="high",
                    message=f"Potential command/code execution pattern matched: {pattern.pattern}",
                    location=str(path),
                    recommendation="Avoid eval/exec or sanitize and strictly validate inputs",
                ))

        for pattern in WEAK_ENV_PATTERNS:
            if pattern.search(content):
                issues.append(SecurityIssue(
                    category="config",
                    severity="medium",
                    message=f"Weak credential/env pattern matched: {pattern.pattern}",
                    location=str(path),
                    recommendation="Replace weak defaults with strong secrets from secure storage",
                ))

        return issues

    def run(self) -> SecurityCheckReport:
        issues: list[SecurityIssue] = []
        scan_roots = [
            self.repo_root / "backend" / "api",
            self.repo_root / "backend" / "server.ts",
            self.repo_root / "ai_bridge",
            self.repo_root / "scripts",
        ]
        extensions = {".ts", ".js", ".mjs", ".cjs", ".sh", ".env", ".example"}

        for root in scan_roots:
            if not root.exists():
                continue
            if root.is_file():
                issues.extend(self._scan_file(root))
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                suffix = path.suffix.lower()
                rel = str(path).replace('\\', '/')
                if '/node_modules/' in rel or '/dist/' in rel or '/__pycache__/' in rel:
                    continue
                if suffix in extensions or path.name.endswith(".env.example"):
                    issues.extend(self._scan_file(path))

        allowed = not any(issue.severity in {"high", "critical"} for issue in issues)
        return SecurityCheckReport(name="static_security", allowed=allowed, issues=issues)
