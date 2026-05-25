from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from ai_bridge.core.security_gate.external_scanners import ExternalScannersCheck


def test_external_scanners_reports_missing_tools_are_silent_in_non_strict_mode(tmp_path: Path, monkeypatch):
    (tmp_path / '.github').mkdir(parents=True, exist_ok=True)
    (tmp_path / '.github' / 'dependabot.yml').write_text('version: 2\nupdates: []\n')

    monkeypatch.setattr('shutil.which', lambda tool: None)

    report = ExternalScannersCheck(tmp_path, require_scanners=False).run()

    assert report.allowed is True
    assert all(i.category != 'scanner' for i in report.issues)


def test_external_scanners_strict_mode_blocks_when_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr('shutil.which', lambda tool: None)

    report = ExternalScannersCheck(tmp_path, require_scanners=True).run()

    assert report.allowed is False
    assert any(i.severity == 'high' for i in report.issues if i.category == 'scanner')


def test_external_scanners_parses_gitleaks_critical(tmp_path: Path, monkeypatch):
    (tmp_path / '.github').mkdir(parents=True, exist_ok=True)
    (tmp_path / '.github' / 'dependabot.yml').write_text('version: 2\nupdates: []\n')

    def fake_which(tool: str):
        return '/usr/bin/' + tool if tool == 'gitleaks' else None

    def fake_run(cmd, cwd, capture_output, text):
        if cmd[0] == 'gitleaks':
            return SimpleNamespace(returncode=1, stdout='[{"RuleID":"generic-api-key","File":"x.env"}]', stderr='')
        return SimpleNamespace(returncode=0, stdout='', stderr='')

    monkeypatch.setattr('shutil.which', fake_which)
    monkeypatch.setattr('subprocess.run', fake_run)

    report = ExternalScannersCheck(tmp_path, require_scanners=False).run()

    assert report.allowed is False
    assert any(i.category == 'secret' and i.severity == 'critical' for i in report.issues)
