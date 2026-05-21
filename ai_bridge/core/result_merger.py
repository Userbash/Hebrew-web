from __future__ import annotations

from .models import AgentResult, TaskStatus


class ResultMerger:
    def merge(self, results: list[AgentResult]) -> dict:
        status = "done" if all(result.status == TaskStatus.DONE for result in results) else "failed"
        files_changed: list[str] = []
        commands_run: list[str] = []
        errors: list[str] = []
        summaries: list[str] = []
        for result in results:
            output = result.output
            summaries.append(str(output.get("summary", "")))
            files_changed.extend(output.get("files_changed", []))
            commands_run.extend(output.get("commands_run", []))
            errors.extend(result.errors)
        return {
            "status": status,
            "summary": " | ".join(s for s in summaries if s),
            "files_changed": sorted(set(files_changed)),
            "commands_run": commands_run,
            "errors": errors,
        }
