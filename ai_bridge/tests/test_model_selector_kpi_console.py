from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.kpi import KPIEvaluator
from ai_bridge.core.model_selector import ModelSelector
from ai_bridge.core.models import Complexity, Priority, Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.user_console import UserConsole


def test_model_selector_uses_critical_model_for_security_task():
    task = Task(TaskType.CODE, TaskInput("security production secret handling"), TaskContext("p", ".", "main"), priority=Priority.CRITICAL)
    choice = ModelSelector().select(task)

    assert choice.complexity == Complexity.CRITICAL
    assert choice.model_name == "gpt-senior-secure"
    assert choice.requires_secondary_review


def test_kpi_reduces_priority_for_low_quality_agent():
    registry = AgentRegistry()
    agent = registry.register("reviewer-1", "reviewer", "local://reviewer", ["review"])
    agent.metrics.quality_score = 0.2
    agent.metrics.test_pass_rate = 0.2
    agent.metrics.error_rate = 0.8

    evaluator = KPIEvaluator(threshold=0.65)
    evaluator.apply_priority_policy(agent)

    assert agent.kpi.agent_kpi < 0.65
    assert agent.metrics.priority_score < 1.0


def test_user_console_reports_agent_state():
    registry = AgentRegistry()
    agent = registry.register("codex-main", "codex", "local://codex", ["code"], model_name="gpt-coding-large")
    task = Task(TaskType.CODE, TaskInput("create module"), TaskContext("p", ".", "main"))

    line = UserConsole().agent_status(agent, task, progress=65, stage="пишет код")

    assert "Агент: codex-main" in line
    assert "Модель: gpt-coding-large" in line
    assert "Прогресс: 65%" in line
