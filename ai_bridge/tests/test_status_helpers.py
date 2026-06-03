from __future__ import annotations

from ai_bridge.core.local_llm_module import LocalLLMModule
from ai_bridge.core.testing_module import TestingModule
from ai_bridge.core.orchestrator import Orchestrator


def test_local_llm_task_profile_mentions_test_work():
    module = LocalLLMModule()
    profile = module.task_profile()
    assert "test" in profile["capabilities"]
    assert any("test" in task for task in profile["primary_tasks"])


def test_orchestrator_status_helpers_expose_modules():
    orchestrator = Orchestrator()
    llm_status = orchestrator.local_llm_status()
    test_status = orchestrator.testing_status()
    design_status = orchestrator.design_learning_status()

    assert "module" in llm_status
    assert "profile" in llm_status
    assert "module" in test_status
    assert "final" in test_status
    assert design_status["status"] == "active"
