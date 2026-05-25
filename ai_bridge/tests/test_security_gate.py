from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from ai_bridge.core.security_gate.authz import PreDeployAuthorization
from ai_bridge.core.security_gate.dependency_audit import DependencyAuditCheck
from ai_bridge.core.security_gate.static_analysis import StaticSecurityCheck


def test_authz_denies_unknown_user(tmp_path: Path, monkeypatch):
    check = PreDeployAuthorization(tmp_path)
    monkeypatch.setattr('getpass.getuser', lambda: 'alice')

    report = check.run({'AI_BRIDGE_DEPLOY_ALLOWED_USERS': 'bob'})

    assert report.allowed is False
    assert any('not allowed to deploy' in item.message for item in report.issues)


def test_dependency_audit_detects_high(monkeypatch, tmp_path: Path):
    (tmp_path / 'backend').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'frontend-react').mkdir(parents=True, exist_ok=True)

    payload = '{"metadata":{"vulnerabilities":{"total":1,"high":1,"critical":0}},"vulnerabilities":{"x":{"severity":"high","via":[{"title":"demo cve"}]}}}'

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout=payload, stderr='')

    monkeypatch.setattr('subprocess.run', fake_run)

    report = DependencyAuditCheck(tmp_path).run()

    assert report.allowed is False
    assert any(issue.category == 'cve' for issue in report.issues)


def test_static_check_flags_eval(tmp_path: Path):
    root = tmp_path / 'backend' / 'api'
    root.mkdir(parents=True, exist_ok=True)
    (root / 'bad.js').write_text('const x = eval(userInput);')

    report = StaticSecurityCheck(tmp_path).run()

    assert report.allowed is False
    assert any(issue.category == 'rce' for issue in report.issues)
