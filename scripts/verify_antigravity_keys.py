import os
from dotenv import load_dotenv
from ai_bridge.core.integrations.antigravity_manager import AntigravityManager
from ai_bridge.core.host_bridge import HostBridge

# Load env files to ensure variables are picked up
load_dotenv(".env.bridge", override=True)
load_dotenv(".env.gemini.local", override=True)

# Verify presence of keys
gemini_key = os.getenv('GEMINI_API_KEY')
google_key = os.getenv('GOOGLE_API_KEY')
print(f"GEMINI_API_KEY set: {bool(gemini_key)}")
print(f"GOOGLE_API_KEY set: {bool(google_key)}")

# Use AntigravityManager to check status
try:
    manager = AntigravityManager(host_bridge=HostBridge())
    status = manager.status()
    print(f"Antigravity Status: {status}")
except Exception as e:
    print(f"Error checking Antigravity: {e}")
