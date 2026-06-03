from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .kernel_protocol import KernelAPI, KernelModule
from .session_memory import MemoryScope


@dataclass(slots=True)
class DesignLearningModule(KernelModule):
    name: str = "design_learning"
    _api: KernelAPI | None = None
    _episodes: list[dict[str, Any]] = field(default_factory=list)
    _patterns: dict[str, dict[str, Any]] = field(default_factory=dict)
    _last_plan: dict[str, Any] = field(default_factory=dict)

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", "[DESIGN_LEARNING] design_learning module loaded")

    def on_unload(self) -> None:
        self._api = None

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        memory = self._api.get_memory() if self._api else None
        if memory is None or not hasattr(memory, "get"):
            return
        try:
            prior = memory.get(MemoryScope.SESSION, "design-learning", "latest_recommendations")
        except Exception:
            prior = None
        if prior:
            context["design_learning_prior"] = prior

    def _chunk_findings(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        for finding in findings:
            category = str(finding.get("category", "unknown"))
            severity = str(finding.get("severity", "low"))
            description = str(finding.get("description", "")).strip()
            evidence = finding.get("evidence") or {}
            chunks.append({
                "category": category,
                "severity": severity,
                "description": description,
                "evidence_keys": sorted(list(evidence.keys())) if isinstance(evidence, dict) else [],
                "micro_action": self._micro_action(category, severity),
            })
        return chunks

    @staticmethod
    def _micro_action(category: str, severity: str) -> dict[str, str]:
        base = {
            "alignment": {"owner": "frontend_design", "action": "align grid columns and centralize composition"},
            "spacing": {"owner": "frontend_design", "action": "rebalance vertical rhythm and collapse voids"},
            "layout": {"owner": "frontend_design", "action": "rebuild layout into dense multi-column grid"},
            "visibility": {"owner": "frontend_design", "action": "increase contrast and introduce stronger hierarchy"},
        }
        return base.get(category, {"owner": "reviewer", "action": "manual visual review and verify accessibility"}) | {"priority": severity}

    def learn_from_audit(self, audit_report: dict[str, Any], *, source: str = "vision_design_audit", session_id: str = "design-learning") -> dict[str, Any]:
        findings = audit_report.get("analysis", {}).get("findings", []) if isinstance(audit_report, dict) else []
        if not isinstance(findings, list):
            findings = []
        chunks = self._chunk_findings([f for f in findings if isinstance(f, dict)])
        profile = {
            "source": source,
            "captured_at": datetime.now(UTC).isoformat(),
            "issue_count": len(chunks),
            "categories": sorted({chunk["category"] for chunk in chunks}),
            "severity_counts": {level: sum(1 for chunk in chunks if chunk["severity"] == level) for level in ["critical", "high", "medium", "low"]},
        }
        recommendations = self.recommend_from_chunks(chunks)
        artifact = {
            "profile": profile,
            "chunks": chunks,
            "recommendations": recommendations,
        }
        self._episodes.append({"source": source, "profile": profile, "recommendations": recommendations})
        self._patterns[source] = artifact
        self._last_plan = artifact

        memory = self._api.get_memory() if self._api else None
        if memory is not None and hasattr(memory, "set"):
            try:
                memory.set(MemoryScope.SESSION, session_id, "latest_design_learning", artifact, ttl_sec=86400)
                memory.set(MemoryScope.SESSION, session_id, "latest_design_recommendations", recommendations, ttl_sec=86400)
                memory.set(MemoryScope.SESSION, session_id, "latest_design_profile", profile, ttl_sec=86400)
            except Exception as exc:
                if self._api:
                    self._api.log("warning", f"[DESIGN_LEARNING] memory write failed: {exc}")

        if self._api:
            self._api.emit_event("design_learning_update", {"source": source, "issue_count": len(chunks), "categories": profile["categories"]})
        return artifact

    def recommend_from_chunks(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        assignments: list[dict[str, Any]] = []
        next_actions: list[str] = []
        used_owners: list[str] = []
        for chunk in chunks:
            micro = chunk.get("micro_action", {})
            owner = str(micro.get("owner", "reviewer"))
            action = str(micro.get("action", "manual review"))
            used_owners.append(owner)
            assignments.append({
                "owner": owner,
                "category": chunk.get("category", "unknown"),
                "severity": chunk.get("severity", "low"),
                "action": action,
                "description": chunk.get("description", ""),
            })
            next_actions.append(action)

        pipeline = [
            {"agent": "planner", "task": "convert visual findings into a prioritized redesign backlog"},
            {"agent": "frontend_design", "task": "apply grid, spacing, and density corrections in layout code"},
            {"agent": "tester", "task": "run browser density and visual regression checks"},
            {"agent": "reviewer", "task": "verify the result against UI rules and accessibility"},
        ]
        if not chunks:
            pipeline.insert(0, {"agent": "local_llm", "task": "confirm no layout drift and archive the baseline"})

        summary = {
            "assigned_owners": sorted(set(used_owners)) if used_owners else ["reviewer"],
            "next_actions": next_actions,
            "pipeline": pipeline,
        }
        return summary

    def finalize(self) -> dict[str, Any]:
        return {
            "status": "active",
            "episodes": len(self._episodes),
            "patterns": self._patterns,
            "last_plan": self._last_plan,
        }
