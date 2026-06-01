from ai_bridge.core.orchestrator import Orchestrator


def test_frontend_engineering_bridge_loaded_and_exposes_frameworks():
    orchestrator = Orchestrator()
    loaded = set(orchestrator.loaded_kernel_modules())
    assert "frontend_engineering_bridge" in loaded

    state = orchestrator.module_manager.finalize()
    bridge = state["frontend_engineering_bridge"]
    assert bridge["status"] == "active"
    assert bridge["bridge_mode"] == "kernel_first"
    assert {"react", "vue", "angular", "svelte", "nextjs", "nuxt", "remix", "astro"}.issubset(set(bridge["frameworks"]))
    assert bridge["quality_gate_min"] == 85
    assert bridge["subsystems"] == 10
