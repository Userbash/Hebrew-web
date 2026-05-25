from __future__ import annotations

from pathlib import Path

from ai_bridge.core.deploy_guard import DeployGuard


def _touch_required(root: Path) -> None:
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "docker-compose.yml").write_text("version: '3.9'\n")
    (root / "scripts" / "build_abstracted.sh").write_text("#!/bin/bash\n")
    (root / "scripts" / "start_manual.sh").write_text("#!/bin/bash\n")


def test_deploy_guard_allows_local_non_ci(tmp_path: Path):
    _touch_required(tmp_path)
    guard = DeployGuard(repo_root=tmp_path)

    result = guard.evaluate({})

    assert result.allowed is True
    assert result.reasons == []


def test_deploy_guard_blocks_github_actions(tmp_path: Path):
    _touch_required(tmp_path)
    guard = DeployGuard(repo_root=tmp_path)

    result = guard.evaluate({"GITHUB_ACTIONS": "true", "GITHUB_WORKFLOW": "CI", "CI": "true"})

    assert result.allowed is False
    joined = "\n".join(result.reasons)
    assert "GITHUB_ACTIONS=true" in joined
    assert "GitHub workflow context" in joined
    assert "CI=true" in joined


def test_deploy_guard_blocks_when_required_files_missing(tmp_path: Path):
    guard = DeployGuard(repo_root=tmp_path)

    result = guard.evaluate({})

    assert result.allowed is False
    assert any("required file not found" in reason for reason in result.reasons)
