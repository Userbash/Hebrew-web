from ai_bridge.core.orchestrator import Orchestrator


def test_ui_modules_are_loaded_into_kernel():
    orchestrator = Orchestrator()
    loaded = set(orchestrator.loaded_kernel_modules())
    assert "ui_design_system" in loaded
    assert "ui_anti_template" in loaded


def test_ui_design_tokens_exposed_in_finalize_state():
    orchestrator = Orchestrator()
    state = orchestrator.module_manager.finalize()
    assert "ui_design_system" in state
    assert state["ui_design_system"]["status"] == "active"
    assert "tokens" in state["ui_design_system"]
