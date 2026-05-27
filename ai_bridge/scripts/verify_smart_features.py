import requests
import json
import time

def verify_smart_features():
    print("=== AI Orchestrator Smart Features Verification ===")
    url = "http://localhost:8000/chat"
    
    # 1. Test Prompt Optimization (requires previous history)
    # First, populate memory
    print("[*] Populating memory with a simple task...")
    requests.post(url, json={
        "user_id": "tester",
        "message": "RESEARCH: Memory implementation patterns",
        "session_id": "smart-session"
    }, timeout=60)
    
    # Second, send a follow-up to see if optimizer triggers
    print("[*] Testing Prompt Optimization & Smart Decomposition...")
    payload = {
        "user_id": "tester",
        "message": "PLAN: Build a complex caching layer using the patterns found in previous research.",
        "session_id": "smart-session"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=90)
        data = response.json()
        print(f"[+] Status: {data.get('status')}")
        # result = data.get("result", {})
        # Note: We look at the logs to confirm [OPTIMIZER] and [DECOMP] events
        print("[!] Check Orchestrator logs for [OPTIMIZER] and [DECOMP] tags.")
        
    except Exception as e:
        print(f"[!] Verification failed: {e}")

if __name__ == "__main__":
    time.sleep(5)
    verify_smart_features()
