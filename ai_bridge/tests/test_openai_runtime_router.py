from __future__ import annotations

import json

from ai_bridge.core.model_selector import ModelSelector
from ai_bridge.core.models import Complexity, Priority, Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.openai_model_registry import OpenAIModelRegistry
from ai_bridge.core.openai_runtime_router import OpenAIRuntimeRouter


def _task(task_type: TaskType = TaskType.CODE, complexity: Complexity = Complexity.MEDIUM) -> Task:
    task = Task(
        task_type,
        TaskInput("implement a focused routing change", []),
        TaskContext("hebrew-web", ".", "main"),
    )
    task.complexity = complexity
    return task


def test_openai_registry_uses_cached_text_models(tmp_path, monkeypatch):
    cache = tmp_path / "openai_models.json"
    cache.write_text(
        json.dumps(
            {
                "ts": 4_102_444_800,
                "models": ["gpt-5-mini", "gpt-4.1-nano", "text-embedding-3-small", "gpt-5.2-codex"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_MODELS_CACHE_PATH", str(cache))
    monkeypatch.setenv("OPENAI_MODELS_CACHE_TTL_SEC", "999999999")

    catalog = OpenAIModelRegistry().get_catalog()

    assert "gpt-5-mini" in catalog.mini
    assert "gpt-4.1-nano" in catalog.nano
    assert "gpt-5.2-codex" in catalog.codex


def test_openai_runtime_router_prefers_light_model_for_low_budget(monkeypatch):
    monkeypatch.setenv("OPENAI_SESSION_TOKEN_BUDGET", "64")
    OpenAIRuntimeRouter._session_token_usage.clear()
    router = OpenAIRuntimeRouter()

    plan = router.build_plan(_task(complexity=Complexity.CRITICAL), "very long prompt" * 100)

    assert plan.reason == "budget_guard_lightweight"
    assert plan.models[0] in {"gpt-5-nano", "gpt-5-mini", "gpt-4.1-nano", "gpt-4.1-mini", "gpt-4o-mini"}


def test_model_selector_openai_auto_is_opt_in(monkeypatch):
    task = _task(TaskType.REVIEW, Complexity.HIGH)
    monkeypatch.delenv("AI_BRIDGE_OPENAI_AUTO_MODEL", raising=False)
    legacy = ModelSelector().select(task)
    assert legacy.model_name == "gpt-coding-large"

    monkeypatch.setenv("AI_BRIDGE_OPENAI_AUTO_MODEL", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_HIGH_MODELS", "gpt-5-mini,gpt-5.1")
    auto = ModelSelector().select(task)

    assert auto.provider == "openai"
    assert auto.model_name == "gpt-5-mini"
    assert auto.reason.startswith("openai_auto_")


def test_model_selector_auto_falls_back_when_openai_key_missing(monkeypatch):
    task = _task(TaskType.REVIEW, Complexity.HIGH)
    monkeypatch.setenv("AI_BRIDGE_OPENAI_AUTO_MODEL", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-test")

    choice = ModelSelector().select(task)

    assert choice.provider == "mistral"
    assert choice.model_name == "mistral-large-latest"
    assert choice.reason.startswith("openai_auto_no_key_mistral_fallback")


def test_provider_budget_router_honors_critical_mistral_fallback(monkeypatch):
    from ai_bridge.core.provider_budget_router import ProviderBudgetRouter

    task = _task(TaskType.CODE, Complexity.CRITICAL)
    task.priority = Priority.CRITICAL
    monkeypatch.setenv("AI_BRIDGE_OPENAI_AUTO_MODEL", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-test")
    choice = ModelSelector().select(task)

    providers = ProviderBudgetRouter().preferred_providers(task, choice)

    assert choice.provider == "mistral"
    assert providers[:3] == ["mistral", "google", "local"]
