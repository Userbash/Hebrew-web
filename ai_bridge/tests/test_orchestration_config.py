from ai_bridge.core.orchestration_config import OrchestrationConfig
from ai_bridge.core.security import SecurityManager
from ai_bridge.scripts.run_orchestrator import build_parser


def test_safe_standard_tasks_do_not_need_confirmation_by_default():
    config = OrchestrationConfig()

    assert config.should_ask_confirmation({"type": "code", "risk_level": "low"}) is False
    assert config.should_ask_confirmation({"type": "test", "risk_level": "medium"}) is False
    assert config.should_ask_confirmation({"type": "docs", "risk_level": "low"}) is False


def test_destructive_external_and_unsafe_tasks_need_confirmation():
    config = OrchestrationConfig()

    assert config.should_ask_confirmation({"action": "database_delete", "risk_level": "low"}) is True
    assert config.should_ask_confirmation({"type": "code", "requires_external_side_effect": True}) is True
    assert config.should_ask_confirmation({"type": "refactor", "risk_level": "unsafe"}) is True
    assert config.should_ask_confirmation({"type": "code", "manual_only": True}) is True


def test_cli_flags_enable_non_interactive_bridge_mode():
    parser = build_parser()
    args = parser.parse_args(["--use-bridge", "--auto", "--yes", "--non-interactive"])
    config = OrchestrationConfig(enabled_by_default=False, ask_confirmation=True, non_interactive=False)

    config.apply_cli_flags(yes=args.yes, auto=args.auto, use_bridge=args.use_bridge, non_interactive=args.non_interactive)

    assert config.enabled_by_default is True
    assert config.default_mode == "ai_bridge"
    assert config.ask_confirmation is False
    assert config.auto_approve_safe_tasks is True
    assert config.non_interactive is True


def test_env_defaults_enable_ai_bridge_without_prompt(monkeypatch):
    monkeypatch.setenv("AI_BRIDGE_ENABLED", "true")
    monkeypatch.setenv("AI_BRIDGE_DEFAULT", "true")
    monkeypatch.setenv("AI_BRIDGE_AUTO_APPROVE", "true")
    monkeypatch.setenv("AI_BRIDGE_NON_INTERACTIVE", "true")
    monkeypatch.setenv("AI_BRIDGE_CONFIRMATION_POLICY", "safe-only")

    config = OrchestrationConfig.from_env()

    assert config.enabled_by_default is True
    assert config.ask_confirmation is False
    assert config.non_interactive is True
    assert config.should_ask_confirmation({"type": "healthcheck", "risk_level": "low"}) is False
    assert config.should_ask_confirmation({"action": "force_push", "risk_level": "medium"}) is True


def test_security_manager_delegates_confirmation_policy():
    security = SecurityManager(orchestration=OrchestrationConfig())

    assert security.should_ask_confirmation({"type": "metrics", "risk_level": "low"}) is False
    assert security.should_ask_confirmation({"action": "secret_change"}) is True
