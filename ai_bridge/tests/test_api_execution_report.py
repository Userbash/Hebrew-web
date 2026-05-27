import asyncio
import sys
import os
import requests
import time

def test_api():
    print("--- ЗАПУСК ИНТЕГРАЦИОННОГО ТЕСТА API ---")
    url = "http://localhost:8000/chat"
    
    # Test 1: Standard routing task
    payload1 = {
        "user_id": "test_script",
        "message": "RESEARCH: test integration format",
        "session_id": "test-session-1"
    }
    
    print("\n[Тест 1] Отправка RESEARCH задачи (Ожидается отчет об исполнении)")
    try:
        response = requests.post(url, json=payload1, timeout=60)
        data = response.json()
        status = data.get("status")
        result = data.get("result", "")
        
        if isinstance(result, dict):
            summary = result.get("summary", "")
        else:
            summary = str(result)
            
        print(f"Status HTTP: {response.status_code}")
        print(f"Task Status: {status}")
        print(f"Response snippet:\n{summary[:300]}...")
        
        if "AI ORCHESTRATOR EXECUTION REPORT" in summary:
            print("✅ УСПЕХ: Баннер успешно встроен в ответ.")
        else:
            print("❌ ОШИБКА: Баннер не найден в ответе.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ ОШИБКА соединения: {e}")
        sys.exit(1)
        
    print("\n--- ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО ---")

if __name__ == "__main__":
    test_api()
