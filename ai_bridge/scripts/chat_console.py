from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv(".env.bridge")

BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:8000")
USER_ID = os.getenv("USER_ID", "engineer_sanya")
SESSION_ID = str(uuid.uuid4())[:8]
QUEUE_PATH = Path(os.getenv("AI_BRIDGE_QUEUE_PATH", "/tmp/ai_bridge_queue.json"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Bridge chat relay console")
    parser.add_argument("--bridge-url", default=BRIDGE_URL, help="Orchestrator base URL")
    parser.add_argument("--user-id", default=USER_ID, help="User identifier")
    parser.add_argument("--session-id", default=SESSION_ID, help="Session identifier")
    parser.add_argument("--relay", action="store_true", default=True, help="Read stdin and relay each line to the orchestrator")
    parser.add_argument("--transport", choices=("auto", "http", "queue", "parallel"), default="auto", help="Transport used to deliver user text to the orchestrator")
    parser.add_argument("--trace", action="store_true", help="Request fulltrace payloads")
    return parser


def _default_transport() -> str:
    return "http"


def _build_payload(message: str, *, user_id: str, session_id: str) -> dict[str, str]:
    return {
        "user_id": user_id,
        "message": message,
        "session_id": session_id,
        "source": "chat_relay",
        "provider": "cli",
        "mode": "orchestrator",
    }


def _send_via_queue(message: str, *, user_id: str, session_id: str) -> dict:
    payload = _build_payload(message, user_id=user_id, session_id=session_id)
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {"status": "queued", "queue_path": str(QUEUE_PATH), "task_id": payload.get("task_id", "unknown")}


def _send_via_websocket(message: str, *, bridge_url: str, user_id: str, session_id: str, trace: bool = False) -> Optional[dict]:
    try:
        import asyncio
        import websockets
    except Exception as exc:
        print(f"\n[!] WebSocket unavailable: {exc}")
        return None

    ws_url = bridge_url.replace("http://", "ws://").replace("https://", "wss://") + ("/chat/ws")
    payload = _build_payload(message, user_id=user_id, session_id=session_id)

    async def _round_trip() -> dict:
        async with websockets.connect(ws_url, open_timeout=10, close_timeout=5) as ws:
            await ws.send(json.dumps(payload))
            response = await asyncio.wait_for(ws.recv(), timeout=40)
            return json.loads(response)

    try:
        return asyncio.run(_round_trip())
    except Exception as exc:
        print(f"\n[!] WebSocket error: {exc}")
        return None


def _send_parallel(message: str, *, bridge_url: str, user_id: str, session_id: str, trace: bool = False) -> Optional[dict]:
    results: list[dict] = []

    http_result = send_to_orchestrator(message, bridge_url=bridge_url, user_id=user_id, session_id=session_id, trace=trace, transport="http")
    if http_result:
        results.append(http_result)

    queue_result = _send_via_queue(message, user_id=user_id, session_id=session_id)
    if queue_result:
        results.append(queue_result)

    ws_result = _send_via_websocket(message, bridge_url=bridge_url, user_id=user_id, session_id=session_id, trace=trace)
    if ws_result:
        results.append(ws_result)

    if results:
        for result in results:
            if isinstance(result, dict) and result.get("status") in {"completed", "processing", "queued", "rejected"}:
                return result
        return results[0]
    return None


def send_to_orchestrator(message: str, *, bridge_url: str, user_id: str, session_id: str, trace: bool = False, transport: str = "auto") -> Optional[dict]:
    """Send raw user text directly to the Orchestrator bridge."""
    if message.strip().lower() == "/stats":
        try:
            response = requests.get(f"{bridge_url}/stats", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            print(f"\n[!] Error fetching stats: {exc}")
            return None

    payload = _build_payload(message, user_id=user_id, session_id=session_id)

    selected_transport = transport
    if selected_transport == "auto":
        # WebSocket-first with HTTP fallback
        ws_result = _send_via_websocket(message, bridge_url=bridge_url, user_id=user_id, session_id=session_id, trace=trace)
        if ws_result:
            return ws_result
        
        # Fallback to HTTP
        selected_transport = "http"

    if selected_transport == "parallel":
        return _send_parallel(message, bridge_url=bridge_url, user_id=user_id, session_id=session_id, trace=trace)

    if selected_transport == "queue":
        return _send_via_queue(message, user_id=user_id, session_id=session_id)

    # HTTP Transport
    endpoint = "/chat/fulltrace" if trace else "/chat"
    try:
        response = requests.post(f"{bridge_url}{endpoint}", json=payload, timeout=40)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("\n[!] Error: Bridge timeout (task is still running in background).")
    except requests.exceptions.ConnectionError:
        print("\n[!] Error: Could not connect to Bridge. Is the orchestrator running?")
    except Exception as exc:
        print(f"\n[!] Unexpected error: {exc}")
    return None


def _print_result(user_input: str, data: dict) -> None:
    if user_input.strip().lower() == "/stats" and data.get("status") == "success":
        stats = data.get("data", {})
        print("\n" + "=" * 50)
        print(f"AI MODEL USAGE STATISTICS (Total: {stats.get('total_tokens_used', 0)} tokens)")
        print("=" * 50)
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
        print("=" * 50)
        return

    task_id = data.get("task_id")
    status = data.get("status")

    if status == "completed":
        result = data.get("result")
        print(f"\n[CORE] (Task: {task_id}):")
        if isinstance(result, dict):
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result)
    elif status == "processing":
        print(f"\n[BRIDGE]: Task {task_id} accepted but still in progress.")
        print("You can send more commands while the core works.")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


def main() -> int:
    args = build_parser().parse_args()
    bridge_url = args.bridge_url.rstrip("/")
    user_id = args.user_id
    session_id = args.session_id
    transport = str(args.transport or "auto").strip().lower()
    trace = bool(args.trace)

    if args.relay or not sys.stdin.isatty():
        for raw in sys.stdin:
            message = raw.strip()
            if not message:
                continue
            if message.lower() in {"exit", "quit", "выход"}:
                break
            data = send_to_orchestrator(message, bridge_url=bridge_url, user_id=user_id, session_id=session_id, trace=trace, transport=transport)
            if data:
                _print_result(message, data)
        return 0

    print("====================================================")
    print(f"   AI Orchestrator Console (Session: {session_id})")
    print("====================================================")
    print("Type your message for the AI and press Enter.")
    print("Type 'exit' or 'quit' to close.")

    while True:
        try:
            user_input = input(f"\n[{user_id}] > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "выход"]:
                print("Closing console...")
                break

            print("... sending to core ...", end="\r")
            data = send_to_orchestrator(user_input, bridge_url=bridge_url, user_id=user_id, session_id=session_id, trace=trace, transport=transport)
            if data:
                _print_result(user_input, data)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
