import pytest
from unittest.mock import MagicMock, patch
from ai_bridge.core.integrations.antigravity_manager import AntigravityManager

def test_antigravity_manager_checks_readiness():
    # Mock HostBridge
    mock_bridge = MagicMock()
    
    manager = AntigravityManager(host_bridge=mock_bridge)
    
    # Mock _run_agy directly on the manager instance
    with patch.object(manager, "_run_agy") as mock_run:
        # Define behavior for models and healthcheck
        def side_effect(args):
            if "models" in args:
                return {"ok": True, "stdout": "model1\nmodel2\n", "stderr": ""}
            # args is ["-p", "healthcheck: ..."]
            if any("healthcheck" in arg for arg in args):
                return {"ok": True, "stdout": "ok", "stderr": ""}
            return {"ok": False}
        mock_run.side_effect = side_effect
        
        # Test readiness check
        assert manager.is_ready() is True
        
        # Test models list
        models = manager.list_models()
        assert "model1" in models
        assert "model2" in models
        
def test_antigravity_manager_handles_not_ready():
    # Mock HostBridge
    mock_bridge = MagicMock()
    
    manager = AntigravityManager(host_bridge=mock_bridge)
    
    with patch.object(manager, "_run_agy") as mock_run:
        # Mock 'agy models' failure
        mock_run.return_value = {"ok": False, "stdout": "", "stderr": "Error"}
        
        # Test readiness check
        assert manager.is_ready() is False
