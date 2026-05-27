import requests
import uuid
import os
from typing import Optional
from dotenv import load_dotenv

# Load settings from .env.bridge if available
load_dotenv(".env.bridge")

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:8000")
USER_ID = os.getenv("USER_ID", "engineer_sanya")
# Consistent session ID for this instance of the console
SESSION_ID = str(uuid.uuid4())[:8]

def send_to_orchestrator(message: str) -> Optional[dict]:
    """Send a message to the Orchestrator via the Bridge API."""
    if message.strip().lower() == "/stats":
        try:
            response = requests.get(f"{BRIDGE_URL}/stats", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"\n[!] Error fetching stats: {e}")
            return None

    payload = {
        "user_id": USER_ID,
        "message": message,
        "session_id": SESSION_ID
    }
    
    try:
        # The bridge handles the long polling wait for us
        response = requests.post(f"{BRIDGE_URL}/chat", json=payload, timeout=40)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("\n[!] Error: Bridge timeout (Task is still running in background).")
    except requests.exceptions.ConnectionError:
        print("\n[!] Error: Could not connect to Bridge. Is chat_bridge.py running?")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
    return None

def main():
    print("====================================================")
    print(f"   AI Orchestrator Console (Session: {SESSION_ID})")
    print("====================================================")
    print("Type your message for the AI and press Enter.")
    print("Type 'exit' or 'quit' to close.")

    while True:
        try:
            user_input = input(f"\n[{USER_ID}] > ").strip()
            
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit', 'выход']:
                print("Closing console...")
                break

            print("... sending to core ...", end="\r")
            
            # Synchronous call to bridge
            data = send_to_orchestrator(user_input)
            
            if data:
                if user_input.strip().lower() == "/stats" and data.get("status") == "success":
                    stats = data.get("data", {})
                    print("\n" + "="*50)
                    print(f"📊 AI MODEL USAGE STATISTICS (Total: {stats.get('total_tokens_used', 0)} tokens)")
                    print("="*50)
                    models = stats.get("models", {})
                    if not models:
                        print("No model usage recorded yet.")
                    for m_name, m_data in models.items():
                        bar_len = 20
                        filled = int(m_data['usage_percentage'] / 100 * bar_len)
                        bar = "█" * filled + "░" * (bar_len - filled)
                        status_icon = "🟢" if m_data['status'] == "ok" else ("🟡" if m_data['status'] == "low" else "🔴")
                        print(f"\n{status_icon} Model: {m_name}")
                        print(f"   Usage: [{bar}] {m_data['usage_percentage']}%")
                        print(f"   Tokens: {m_data['used_tokens']} used / {m_data['remaining_tokens']} left")
                        print(f"   Requests: {m_data['requests_count']}")
                    print("="*50)
                    continue

                task_id = data.get("task_id")
                status = data.get("status")
                
                if status == "completed":
                    result = data.get("result")
                    print(f"\n[CORE] (Task: {task_id}):")
                    # If result is complex (dict), pretty print it
                    if isinstance(result, dict):
                        import json
                        print(json.dumps(result, indent=2, ensure_ascii=False))
                    else:
                        print(result)
                
                elif status == "processing":
                    print(f"\n[BRIDGE]: Task {task_id} accepted but still in progress.")
                    print("You can send more commands while the core works.")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
