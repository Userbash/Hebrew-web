from ai_bridge.core.integrations.mistral_manager import MistralManager
from dotenv import load_dotenv
import os

load_dotenv(".env.gemini.local")
print(f"Loaded key: {os.getenv('MISTRAL_API_KEY')}")

manager = MistralManager()
try:
    print(f"Status: {manager.status()}")
except Exception as e:
    print(f"Error: {e}")
