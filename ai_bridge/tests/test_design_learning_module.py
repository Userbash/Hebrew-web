from ai_bridge.core.integrations.design_learning_module import DesignLearningModule, DesignSample
from ai_bridge.core.session_memory import SessionMemory


def test_design_learning_improves_confidence_for_framework():
    module = DesignLearningModule(SessionMemory())
    module.add_sample(
        DesignSample(
            project_id="p1",
            framework="react",
            image_labels=["saas", "dashboard", "clean"],
            user_feedback_score=0.9,
        )
    )
    result = module.suggest_ui_direction("react")
    assert result["style"] == "data-trained-modern"
    assert result["confidence"] > 0.7
    assert "dashboard" in result["tokens"]
