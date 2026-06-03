from __future__ import annotations

from ai_bridge.core.design_learning_module import DesignLearningModule
from ai_bridge.core.orchestrator import Orchestrator


def test_design_learning_module_turns_findings_into_actions():
    module = DesignLearningModule()
    report = {
        "analysis": {
            "findings": [
                {"severity": "high", "category": "alignment", "description": "left rail dominates", "evidence": {"asymmetry": 0.42}},
                {"severity": "medium", "category": "spacing", "description": "vertical gaps are uneven", "evidence": {"asymmetry": 0.31}},
            ]
        }
    }

    artifact = module.learn_from_audit(report)

    assert artifact["profile"]["issue_count"] == 2
    assert "alignment" in artifact["profile"]["categories"]
    assert artifact["recommendations"]["pipeline"][1]["agent"] == "frontend_design"
    assert len(artifact["recommendations"]["next_actions"]) == 2


def test_orchestrator_exposes_design_learning_module():
    orchestrator = Orchestrator()
    module = orchestrator.get_module("design_learning")

    assert module is not None
    status = orchestrator.design_learning_status()
    assert status["status"] == "active"
