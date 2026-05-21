from __future__ import annotations

from .models import AgentResult, QualityReport, Task, TaskStatus
from .security import SecurityManager


class QualityAnalyzer:
    def __init__(self, security: SecurityManager | None = None, minimum_confidence: float = 0.7) -> None:
        self.security = security or SecurityManager()
        self.minimum_confidence = minimum_confidence

    def analyze(self, task: Task, result: AgentResult) -> QualityReport:
        issues: list[str] = []
        output = result.output
        text = "\n".join([str(output.get("summary", "")), str(output.get("diff", "")), "\n".join(result.errors)])
        if result.status != TaskStatus.DONE:
            issues.append("result_status_not_done")
        if result.confidence < self.minimum_confidence:
            issues.append("low_confidence")
        if self.security.redact_secrets(text) != text:
            issues.append("possible_secret_leakage")
        if not output.get("summary"):
            issues.append("missing_summary")
        if task.input.acceptance_criteria and result.status == TaskStatus.DONE and result.confidence < 0.8:
            issues.append("acceptance_needs_review")
        score = max(0.0, result.confidence - len(issues) * 0.15)
        return QualityReport(passed=not issues, score=score, issues=issues, requires_review=bool(issues))
