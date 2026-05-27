import requests
import json
import concurrent.futures
import time
import random
import uuid

def send_task(priority="normal", session_id="stress-test"):
    url = "http://localhost:8000/chat"
    task_id = str(uuid.uuid4())
    payload = {
        "user_id": "stress_tester",
        "message": f"{priority.upper()}: Perform deep analysis of component {task_id[:8]}",
        "session_id": session_id
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        return response.status_code, response.json()
    except Exception as e:
        return 500, str(e)

def run_stress_test():
    print("=== ORCHESTRATOR CORE STRESS TEST ===")
    
    # 1. Agent Priority Concurrency
    print("[*] Phase 1: Concurrency & Priority Routing...")
    priorities = ["low", "normal", "high", "critical"]
    tasks = []
    for _ in range(20):
        tasks.append(random.choice(priorities))
        
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_task, p) for p in tasks]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    duration = time.time() - start_time
    success_count = sum(1 for r in results if r[0] == 200)
    print(f"[+] Concurrency Test: {success_count}/{len(tasks)} succeeded in {duration:.2f}s")

    # 2. VFS & Themes Integrity Check
    print("\n[*] Phase 2: VFS & Themes Integrity Check...")
    try:
        with open("memory_store/themes.json", "r") as f:
            themes = json.load(f)
            print(f"[+] Themes.json entries: {len(themes)}")
    except Exception as e:
        print(f"[!] Themes.json error: {e}")
        
    import os
    vfs_files = os.listdir("memory_store/vfs")
    print(f"[+] VFS Checkpoints found: {len(vfs_files)}")

    # 3. Memory Eviction & Search Test
    print("\n[*] Phase 3: Memory Eviction & Search (Direct Core Test)...")
    # We will trigger many memory writes to force eviction (max is 2000)
    # We use python -c to talk to the core directly since it's in the same env
    eviction_cmd = """
from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.core.models import Task, TaskInput, TaskContext, TaskType
import uuid
import time

orch = Orchestrator()
mem = orch.session_memory.hybrid

print(f'Starting Cache: {len(mem._hot)} entries')

# Flood memory to trigger eviction
for i in range(2500):
    mem.set('session', 'stress', f'key_{i}', {'data': 'x' * 100}, importance_score=0.1)

print(f'Cache after flooding: {len(mem._hot)} entries')
evicted = mem.run_maintenance_once()
print(f'Forced Maintenance evicted: {evicted} entries')
print(f'Cache after maintenance: {len(mem._hot)} entries')

# Search test
hits = mem.fast_retrieve(query_text='key_2400', session_id='stress')
print(f'Search result for key_2400: {len(hits)} hits (Expected >= 1)')
"""
    import subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "") + ":."
    proc = subprocess.run(["python3", "-c", eviction_cmd], capture_output=True, text=True, env=env)
    print(proc.stdout)
    if proc.stderr:
        print(f"[!] Error in memory test: {proc.stderr}")

if __name__ == "__main__":
    run_stress_test()
