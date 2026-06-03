from __future__ import annotations

from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.core.testing_module import TestingModule


def test_orchestrator_exposes_testing_module():
    orchestrator = Orchestrator()
    module = orchestrator.get_module("testing")
    assert isinstance(module, TestingModule)


def test_testing_module_run_suite_can_be_mocked(monkeypatch, tmp_path):
    module = TestingModule()

    def fake_run(cmd, cwd=None):
        return {
            "command": cmd,
            "cwd": str(cwd),
            "returncode": 0,
            "stdout": "ok",
            "stderr": "",
            "ok": True,
        }

    monkeypatch.setattr(module, "_run", fake_run)
    result = module.run_suite(tmp_path)

    assert result["ok"] is True
    assert set(result["results"].keys()) == {"core_healthcheck", "verify_core", "pytest"}
