from ai_bridge.core.security import SecurityManager, SecurityPolicy


def test_shell_command_allowlist_and_blocklist():
    security = SecurityManager(SecurityPolicy(allow_shell=True, shell_allowlist=["pytest", "npm test"]))

    assert security.validate_shell_command("pytest ai_bridge/tests")
    assert not security.validate_shell_command("sudo pytest")
    assert not security.validate_shell_command("rm -rf /")


def test_secret_redaction_and_external_context_filtering():
    security = SecurityManager()
    context = {"project": "demo", "api_key": "abc", "note": "token=secret123"}

    safe = security.safe_context_for_external_ai(context)

    assert "api_key" not in safe
    assert safe["note"] == "[REDACTED]"
