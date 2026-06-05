from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass(slots=True)
class SmokeResult:
    ok: bool
    url: str
    status_code: int | None
    payload: dict[str, Any]
    error_message: str | None = None


def _base_url() -> str:
    return os.getenv("AI_BRIDGE_API_URL", "http://127.0.0.1:8000").rstrip("/")


def _http_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout_sec: float = 10.0) -> SmokeResult:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method=method)
    try:
        with request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8")
            parsed: dict[str, Any]
            if raw.strip():
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    parsed = {"raw": raw}
            else:
                parsed = {}
            return SmokeResult(True, url, getattr(resp, "status", None), parsed)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
        parsed = {"raw": raw} if raw else {}
        return SmokeResult(False, url, exc.code, parsed, f"HTTP {exc.code}: {exc.reason}")
    except Exception as exc:
        return SmokeResult(False, url, None, {}, str(exc))


def run_smoke_check(base_url: str, timeout_sec: float = 10.0) -> int:
    endpoints = [
        ("GET", f"{base_url}/sourcecraft", None),
        ("POST", f"{base_url}/sourcecraft/delegate", {
            "description": "Prepare SourceCraft release notes and repo status",
            "task_type": "plan",
            "priority": "normal",
            "repo_path": ".",
            "branch": "main",
            "files": [],
            "constraints": ["smoke-check"],
            "acceptance_criteria": ["SourceCraft delegation succeeds"],
            "required_capability": "sourcecraft",
        }),
    ]

    results: list[SmokeResult] = []
    for method, url, payload in endpoints:
        results.append(_http_json(method, url, payload, timeout_sec=timeout_sec))

    ok = True
    print("SourceCraft Smoke Check")
    print(f"Base URL: {base_url}")
    for result in results:
        label = result.url.rsplit("/", 1)[-1]
        if result.ok:
            print(f"[{label}] OK status={result.status_code}")
        else:
            print(f"[{label}] FAIL status={result.status_code} error={result.error_message}")
            ok = False
            continue

        if result.url.endswith("/sourcecraft"):
            status = str(result.payload.get("status", "unknown"))
            role = result.payload.get("role", {}) if isinstance(result.payload.get("role"), dict) else {}
            print(f"  sourcecraft_status={status} role={role.get("name", "unknown")}")
            if status == "error":
                ok = False
        elif result.url.endswith("/sourcecraft/delegate"):
            route = result.payload.get("route", {}) if isinstance(result.payload.get("route"), dict) else {}
            schedule = result.payload.get("schedule", {}) if isinstance(result.payload.get("schedule"), dict) else {}
            print(f"  assigned_agent={route.get("assigned_agent", "unknown")} route_mode={schedule.get("route_mode", "unknown")}")
            if result.payload.get("status") != "ok" or route.get("assigned_agent") not in {"orchestrator", None} and schedule.get("route_mode") != "orchestrator":
                ok = False

    print("RESULT: OK" if ok else "RESULT: FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the SourceCraft API endpoints on the orchestrator.")
    parser.add_argument("--base-url", default=_base_url(), help="Orchestrator base URL, default: %(default)s")
    parser.add_argument("--timeout-sec", type=float, default=10.0, help="HTTP timeout in seconds")
    args = parser.parse_args(argv)
    return run_smoke_check(args.base_url, timeout_sec=args.timeout_sec)


if __name__ == "__main__":
    raise SystemExit(main())
