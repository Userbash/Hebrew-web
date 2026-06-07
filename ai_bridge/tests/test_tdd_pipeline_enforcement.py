import pytest
from pathlib import Path
from ai_bridge.core.autodev_pipeline_module import AutodevPipelineModule

def test_pipeline_enforces_tdd_cycle_no_tests(tmp_path: Path):
    pipeline = AutodevPipelineModule()
    specs = "Implement a feature that adds 1+1"
    result = pipeline.run_pipeline(specs, tmp_path)
    assert result["status"] == "failed"
    assert "No failing test" in str(result.get("state", {}).get("errors", [{}])[0])

def test_pipeline_enforces_tdd_cycle_green_tests(tmp_path: Path):
    pipeline = AutodevPipelineModule()
    
    # Create a test file that passes
    test_file = tmp_path / "test_feature.py"
    test_file.write_text("def test_always_pass(): assert True")
    
    specs = "Implement a feature that adds 1+1"
    result = pipeline.run_pipeline(specs, tmp_path)
    
    # Should fail because it's already GREEN
    assert result["status"] == "failed"
    assert "Tests are already GREEN" in str(result.get("state", {}).get("errors", [{}])[0])

def test_pipeline_enforces_tdd_cycle_red_tests(tmp_path: Path):
    pipeline = AutodevPipelineModule()
    
    # Create a test file that fails
    test_file = tmp_path / "test_feature.py"
    test_file.write_text("def test_always_fail(): assert False")
    
    specs = "Implement a feature that adds 1+1"
    # This should pass the TDD check and proceed to the pipeline loop (which might fail due to iterations)
    result = pipeline.run_pipeline(specs, tmp_path)
    
    # It should NOT fail the initial TDD check.
    # It might fail the pipeline execution itself (iteration limit), but the TDD check must pass.
    errors = result.get("state", {}).get("errors", [])
    tdd_errors = [e for e in errors if "No failing test" in str(e) or "Tests are already GREEN" in str(e)]
    assert len(tdd_errors) == 0
