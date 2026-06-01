from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENV = ROOT / ".venv_ai_bridge"
REPORT = ROOT / "ai_bridge" / "runtime_report.json"
REQS = [
    ROOT / "ai_bridge" / "requirements-ai.txt",
    ROOT / "requirements-core.txt",
]

CORE_MODULES = [
    "ai_bridge/core/orchestrator.py",
    "ai_bridge/core/task_router.py",
    "ai_bridge/core/smart_scheduler.py",
    "ai_bridge/core/agent_registry.py",
    "ai_bridge/core/agent_lifecycle.py",
    "ai_bridge/core/model_selector.py",
    "ai_bridge/core/provider_budget_router.py",
    "ai_bridge/core/api_bridge_module.py",
    "ai_bridge/core/task_submission_api.py",
    "ai_bridge/core/session_memory.py",
    "ai_bridge/core/persistent_memory.py",
]


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, env=env, text=True, capture_output=True)


def create_venv() -> None:
    if not VENV.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)], cwd=ROOT)


def pip_bin() -> str:
    return str(VENV / "bin" / "pip")


def py_bin() -> str:
    return str(VENV / "bin" / "python")


def install_requirements() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    subprocess.check_call([pip_bin(), "install", "--upgrade", "pip", "setuptools", "wheel", "pytest"], cwd=ROOT)
    for req in REQS:
        if req.exists():
            proc = run([pip_bin(), "install", "-r", str(req)])
            results.append({"file": str(req), "rc": str(proc.returncode), "stderr": proc.stderr[-4000:]})
            if proc.returncode != 0:
                raise RuntimeError(f"Dependency install failed: {req}\n{proc.stderr}")
    return results


def inventory() -> dict[str, object]:
    files = []
    for rel in CORE_MODULES:
        p = ROOT / rel
        files.append({"module": rel, "exists": p.exists(), "size": p.stat().st_size if p.exists() else 0})
    return {"core_modules": files}


def healthcheck() -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    proc = run([py_bin(), "-m", "pytest", "ai_bridge/tests/test_task_submission_api.py", "ai_bridge/tests/test_kernel_modules.py", "-q"], env=env)
    return {"rc": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}


def main() -> int:
    report: dict[str, object] = {"root": str(ROOT)}
    report.update(inventory())
    try:
        create_venv()
        report["venv"] = str(VENV)
        report["deps"] = install_requirements()
        report["tests"] = healthcheck()
        report["ok"] = report["tests"]["rc"] == 0
    except Exception as exc:
        report["ok"] = False
        report["error"] = str(exc)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(REPORT))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
