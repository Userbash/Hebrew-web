from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SecurityIssue:
    category: str
    severity: str
    message: str
    location: str | None = None
    recommendation: str | None = None


@dataclass(slots=True)
class SecurityCheckReport:
    name: str
    allowed: bool
    issues: list[SecurityIssue] = field(default_factory=list)


@dataclass(slots=True)
class SecurityGateReport:
    allowed: bool
    reports: list[SecurityCheckReport] = field(default_factory=list)

    def flattened_issues(self) -> list[SecurityIssue]:
        items: list[SecurityIssue] = []
        for report in self.reports:
            items.extend(report.issues)
        return items
