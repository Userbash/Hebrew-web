from ai_bridge.core.integrations import FrontendFrameworkModules, ImageMLOrchestrator


def test_recognition_fallback_works_with_heuristics():
    orchestrator = ImageMLOrchestrator()
    result = orchestrator.recognize(b"demo-image-bytes", {"hint": "dashboard"})
    assert result.backend in {"tensorflow", "pytorch", "onnxruntime", "heuristic"}
    assert result.labels
    assert 0.0 < result.confidence <= 1.0


def test_training_schedule_validation():
    orchestrator = ImageMLOrchestrator()
    payload = orchestrator.train("dataset://frontend-components", epochs=3)
    assert payload["status"] == "scheduled"
    assert payload["epochs"] == 3


def test_frontend_module_registry_supports_common_frameworks():
    modules = FrontendFrameworkModules()
    assert modules.get("react").recognizer_api == "/api/ml/recognize"
    assert {"react", "vue", "angular", "svelte", "nextjs", "nuxt", "remix", "astro"}.issubset(set(modules.supported()))
