from ai_bridge.core.integrations.mistral_manager import MistralManager
from dotenv import load_dotenv
import os
import httpx

# Explicitly load the bridge file
load_dotenv(".env.bridge", override=True)
key = os.getenv('MISTRAL_API_KEY')
print(f"Loaded key from .env.bridge: {key[:5]}...{key[-5:] if key else 'None'}")

manager = MistralManager(api_key=key)
try:
    # Детальная проверка через httpx напрямую для диагностики
    response = httpx.get(f"{manager.base_url}/models", headers=manager._get_headers(), timeout=5.0)
    print(f"API Response Code: {response.status_code}")
    print(f"API Response Body: {response.text}")
    print(f"Manager Status: {manager.status()}")
except Exception as e:
    print(f"Error: {e}")
