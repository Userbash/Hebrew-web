import requests
import json
import concurrent.futures
import time

def send_request(task_name, message, priority="normal"):
    url = "http://localhost:8000/chat"
    payload = {
        "user_id": "load_tester",
        "message": f"{priority.upper()}: {message}",
        "session_id": "load-test-session"
    }
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=120)
        end_time = time.time()
        return {
            "task": task_name,
            "status_code": response.status_code,
            "duration": end_time - start_time,
            "data": response.json()
        }
    except Exception as e:
        return {
            "task": task_name,
            "error": str(e)
        }

def run_load_test():
    print("=== AI Orchestrator Load & Priority Test ===")
    
    tasks = [
        ("T1", "RESEARCH: How to implement a robust message bus in Python", "low"),
        ("T2", "DOCS: Document the current API structure", "low"),
        ("T3", "CODE: Implement a simple hello world in Python", "normal"),
        ("T4", "FIX: Fix a potential null pointer in server.ts", "high"),
        ("T5", "SECURITY: Audit the database migration scripts", "critical"),
        ("T6", "ARCH: Design a multi-tenant SaaS architecture", "critical"),
    ]
    
    print(f"[*] Sending {len(tasks)} tasks concurrently...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        future_to_task = {executor.submit(send_request, t[0], t[1], t[2]): t for t in tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            results.append(future.result())
            
    print("\n--- Test Results ---")
    for res in results:
        if "error" in res:
            print(f"Task {res['task']}: FAILED - {res['error']}")
        else:
            data = res['data']
            task_id = data.get("task_id", "unknown")
            status = data.get("status", "unknown")
            # In the new API structure, the agent might be in the result object
            result_obj = data.get("result", {})
            agent_id = result_obj.get("agent_id", "unknown")
            print(f"Task {res['task']}: Status={res['status_code']}, ID={task_id}, Agent={agent_id}, Time={res['duration']:.2f}s")

if __name__ == "__main__":
    run_load_test()
