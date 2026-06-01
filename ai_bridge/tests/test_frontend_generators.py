from pathlib import Path

from ai_bridge.core.component_codegen_module import ComponentCodegenModule
from ai_bridge.core.frontend_scaffold_generator import FrontendScaffoldGenerator


def test_frontend_scaffold_generator_creates_react_vite_shape(tmp_path: Path):
    gen = FrontendScaffoldGenerator()
    out = gen.generate(str(tmp_path / "app"), app_name="ls-app")
    assert out["status"] == "generated"
    assert (tmp_path / "app" / "package.json").exists()
    assert (tmp_path / "app" / "vite.config.ts").exists()
    assert (tmp_path / "app" / "src" / "App.tsx").exists()


def test_component_codegen_generates_ui_components(tmp_path: Path):
    gen = ComponentCodegenModule()
    out = gen.generate(str(tmp_path / "app"), {"components": [{"name": "Panel"}, {"name": "MetricCard"}]})
    assert out["status"] == "generated"
    assert out["count"] == 2
    assert (tmp_path / "app" / "src" / "components" / "ui" / "Panel.tsx").exists()
