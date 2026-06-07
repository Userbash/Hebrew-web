import pytest
import os
from unittest.mock import MagicMock, patch
from ai_bridge.core.integrations.mistral_manager import MistralManager

def test_mistral_manager_checks_readiness_success():
    with patch("httpx.get") as mock_get:
        # Имитируем успешный ответ API Mistral
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"data": [{"id": "mistral-tiny"}, {"id": "mistral-small"}]})
        
        manager = MistralManager(api_key="fake-key")
        
        # Test readiness check
        assert manager.is_ready() is True
        
        # Test models list
        models = manager.list_models()
        assert "mistral-tiny" in models
        assert "mistral-small" in models
        
def test_mistral_manager_handles_auth_failure():
    with patch("httpx.get") as mock_get:
        # Имитируем ошибку авторизации
        mock_get.return_value = MagicMock(status_code=401)
        
        manager = MistralManager(api_key="wrong-key")
        
        # Test readiness check
        assert manager.is_ready() is False
