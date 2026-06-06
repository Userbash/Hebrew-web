from __future__ import annotations

from types import SimpleNamespace

from ai_bridge.core.local_llm_module import LocalLLMModule
from ai_bridge.core.orchestrator import Orchestrator


class _Console:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def info(self, tag: str, message: str) -> None:
        self.messages.append((tag, message))

    def warning(self, tag: str, message: str) -> None:
        self.messages.append((tag, message))

    def emit(self, tag: str, message: str) -> None:
        self.messages.append((tag, message))


def test_autostart_local_llm_invokes_bridge(monkeypatch):
    module = LocalLLMModule(model_name="qwen2.5:32b-instruct-q4_k_m")
    bridge_calls: list[str] = []

    def fake_ensure_ready(model_name: str) -> bool:
        bridge_calls.append(model_name)
        return True

    monkeypatch.setattr(Orchestrator, "_local_llm_autostart_enabled", staticmethod(lambda: True))
    monkeypatch.setenv("TESTING", "false")

    orchestrator = Orchestrator.__new__(Orchestrator)
    orchestrator.console = _Console()
    orchestrator.module_manager = SimpleNamespace(get_module=lambda name: module)
    orchestrator.local_llm_bridge = SimpleNamespace(ensure_ready=fake_ensure_ready)
    orchestrator.log = Orchestrator.log.__get__(orchestrator, Orchestrator)

    Orchestrator._autostart_local_llm(orchestrator)

    assert bridge_calls == ["qwen2.5:32b-instruct-q4_k_m"]
    assert any("Autostart complete" in message for _, message in orchestrator.console.messages)





def test_local_llm_decomposition_task_plan_uses_draft(monkeypatch):
    from ai_bridge.core.models import Complexity, Priority, Task, TaskContext, TaskInput, TaskType
    from ai_bridge.core.task_decomposer import TaskDecomposer

    draft = {
        "status": "model",
        "layers": [
            {
                "name": "intake",
                "objective": "Normalize the request",
                "capability": "plan",
                "task_type": "plan",
                "dependencies": [],
                "sub_agents": ["planner"],
            },
            {
                "name": "verification",
                "objective": "Prepare test coverage",
                "capability": "test",
                "task_type": "test",
                "dependencies": ["intake"],
                "sub_agents": ["tester"],
            },
        ],
    }

    module = LocalLLMModule(model_name="qwen2.5:32b-instruct-q4_k_m")
    monkeypatch.setattr(module, "check_health", lambda: {"ok": True, "model_present": True, "status_code": 200, "available_models": [module.model_name]})
    monkeypatch.setattr(module, "build_decomposition_draft", lambda task, context=None: {**draft, "ready": True, "task_family": "planning", "actions": ["break down task"], "core_retained_actions": ["security enforcement"], "recommended_model": module.model_name, "summary": "split the work", "context_digest": "short", "next_steps": ["plan", "test"], "model_hint": module.model_name})

    task = Task(
        task_id="task-smoke",
        type=TaskType.PLAN,
        priority=Priority.NORMAL,
        complexity=Complexity.MEDIUM,
        input=TaskInput(
            "Create a plan and tests for local LLM startup",
            files=["ai_bridge/core/local_llm_bridge.py"],
            acceptance_criteria=["plan and test tasks exist"],
        ),
        context=TaskContext("smoke", ".", "main"),
    )

    plan = TaskDecomposer().decompose(task, {"local_llm": module.build_decomposition_draft(task)})

    assert [atomic.type.value for atomic in plan.atomic_tasks] == ["plan", "test"]
    assert plan.atomic_tasks[1].dependencies == [plan.atomic_tasks[0].task_id]
    assert plan.atomic_tasks[0].routing_hints["source"] == "local_llm"

def test_local_llm_bridge_auto_provisions_missing_container(monkeypatch):
    from ai_bridge.core.local_llm_bridge import LocalLLMBridge
    from types import SimpleNamespace

    bridge = LocalLLMBridge(container_name="ai-kernel-local", ollama_port=11434)
    calls: list[str] = []

    monkeypatch.setenv("AI_BRIDGE_LOCAL_LLM_AUTO_PROVISION", "true")
    monkeypatch.setattr(LocalLLMBridge, "container_exists", lambda self: False)
    monkeypatch.setattr(LocalLLMBridge, "_host_probe", lambda self: {"ok": True})
    monkeypatch.setattr(LocalLLMBridge, "is_model_downloaded", lambda self, model_name: True)
    monkeypatch.setattr(LocalLLMBridge, "_run", lambda self, args, check=False: SimpleNamespace(returncode=0, stdout="", stderr=""))

    monkeypatch.setattr("ai_bridge.core.local_llm_bridge.deploy_local_llm.ensure_container", lambda name: calls.append(f"ensure:{name}"))
    monkeypatch.setattr("ai_bridge.core.local_llm_bridge.deploy_local_llm.install_ollama", lambda name: calls.append(f"install:{name}"))
    monkeypatch.setattr("ai_bridge.core.local_llm_bridge.deploy_local_llm.start_service", lambda name: calls.append(f"start:{name}"))

    assert bridge.ensure_ready("qwen2.5:32b-instruct-q4_k_m") is True
    assert calls == ["ensure:ai-kernel-local", "install:ai-kernel-local", "start:ai-kernel-local"]
