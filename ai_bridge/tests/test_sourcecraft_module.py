from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.core.sourcecraft_module import SourceCraftModule


class _FakeAPI:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def log(self, level: str, message: str) -> None:
        self.messages.append((level, message))


def _make_src_script(path: Path, body: str) -> None:
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o755)


def test_sourcecraft_module_reports_ready_and_exposes_context(tmp_path, monkeypatch):
    src = tmp_path / "src"
    _make_src_script(src, 'echo "Version: 0.1.2"')
    monkeypatch.setenv("SOURCECRAFT_CLI_BIN", str(src))

    module = SourceCraftModule()
    api = _FakeAPI()
    module.on_load(api)

    context: dict[str, object] = {}
    task = SimpleNamespace(type=SimpleNamespace(value="code"), input=SimpleNamespace(description="Create a PR for repo release automation"))
    module.before_task(task, context)

    final = module.finalize()

    assert final["status"] == "ready"
    assert final["version"] == "Version: 0.1.2"
    assert final["binary"] == str(src)
    assert final["role"]["name"] == "sourcecraft"
    assert "repository operations" in final["role"]["summary"].lower() or "repository" in final["role"]["summary"].lower()
    assert context["sourcecraft"]["enabled"] is True
    assert context["sourcecraft"]["likely_repo_work"] is True
    assert context["sourcecraft"]["role"]["name"] == "sourcecraft"
    assert context["sourcecraft"]["delegation"]["recommended_owner"] == "sourcecraft"
    assert context["sourcecraft"]["delegation"]["should_delegate"] is True
    assert context["sourcecraft"]["automation"]["owner"] == "sourcecraft"
    assert any("SOURCECRAFT" in message for _, message in api.messages)


def test_sourcecraft_module_gracefully_degrades_when_binary_missing(monkeypatch):
    monkeypatch.setenv("SOURCECRAFT_CLI_BIN", "/nonexistent/sourcecraft-src")

    module = SourceCraftModule()
    module.on_load(_FakeAPI())

    final = module.finalize()

    assert final["status"] == "error"
    assert final["binary"] is None
    assert "not found" in str(final["last_error"])


def test_sourcecraft_module_builds_delegation_profile():
    from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskType

    module = SourceCraftModule()
    module._status = "ready"
    task = Task(TaskType.PLAN, TaskInput("Prepare repo status, PR draft, and release notes"), TaskContext("demo", ".", "main"), required_capability="sourcecraft")

    profile = module.build_delegation_profile(task, {"description": task.input.description})

    assert profile["should_delegate"] is True
    assert profile["recommended_owner"] == "sourcecraft"
    assert profile["task_family"] == "repo_ops"
    assert "summarize repository state" in profile["sourcecraft_actions"]


def test_orchestrator_registers_sourcecraft_module():
    orchestrator = Orchestrator()

    assert "sourcecraft" in orchestrator.loaded_kernel_modules()
    state = orchestrator.module_manager.finalize()
    assert "sourcecraft" in state


def test_task_decomposer_auto_marks_sourcecraft_repo_tasks():
    from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskType
    from ai_bridge.core.task_decomposer import TaskDecomposer

    task = Task(TaskType.PLAN, TaskInput("Prepare release notes and PR flow for repo status"), TaskContext("demo", ".", "main"))
    plan = TaskDecomposer().decompose(task)

    assert plan.atomic_tasks[0].required_capability == "sourcecraft"
    assert plan.atomic_tasks[1].required_capability == "code"


def test_api_bridge_sourcecraft_delegate_preview():
    from ai_bridge.core.api_bridge_module import APIBridgeModule, SourceCraftDelegateRequest
    from ai_bridge.core.models import TaskAcceptance, TaskStatus

    class _Router:
        def route(self, task):
            return TaskAcceptance(task.task_id, TaskStatus.ACCEPTED, "orchestrator", "high", "preview")

    class _Scheduler:
        def schedule(self, task):
            from ai_bridge.core.models import SchedulerDecision
            return SchedulerDecision(task.task_id, "orchestrator", None, True, "preview", 9.0)

    class _FakeAPI2:
        def __init__(self):
            self.router = _Router()
            self.scheduler = _Scheduler()
            self.sourcecraft = SourceCraftModule()
            self.sourcecraft.on_load(_FakeAPI())

        def get_module(self, name):
            if name == "sourcecraft":
                return self.sourcecraft
            return None

        def get_context(self, key):
            return getattr(self, key, None)

    module = APIBridgeModule()
    module._api = _FakeAPI2()
    response = module._sourcecraft_delegate(SourceCraftDelegateRequest(description="Prepare SourceCraft release notes for repo status", task_type="plan", repo_path=".", branch="main"))

    assert response["status"] == "ok"
    assert response["sourcecraft"]["role"]["name"] == "sourcecraft"
    assert response["delegation"]["recommended_owner"] == "sourcecraft"
    assert response["delegation"]["should_delegate"] is True
    assert response["route"]["assigned_agent"] == "orchestrator"
    assert response["schedule"]["route_mode"] == "orchestrator"


def test_task_decomposer_marks_sourcecraft_dag_nodes_in_context():
    from ai_bridge.core.models import Priority, SecurityPolicy, TaskPayload, encapsulate
    from ai_bridge.core.task_decomposer import TaskDecomposer

    payload = TaskPayload(
        objective="Prepare SourceCraft release notes for repo status",
        input_data={"repo": "."},
        context={"branch": "main"},
        acceptance_criteria=["release notes prepared"],
        expected_output_format="json",
    )
    envelope = encapsulate(
        payload,
        {
            "target_capability": "sourcecraft",
            "priority": Priority.NORMAL,
            "security_policy": SecurityPolicy(),
        },
    )

    graph = TaskDecomposer().decompose_to_graph(envelope)

    assert graph.nodes
    assert all(node.payload.context.get("sourcecraft_role") is True for node in graph.nodes.values())
    assert all(node.payload.context.get("sourcecraft_role_name") == "sourcecraft" for node in graph.nodes.values())


def test_task_decomposer_uses_local_llm_layered_draft():
    from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskType
    from ai_bridge.core.task_decomposer import TaskDecomposer

    task = Task(TaskType.PLAN, TaskInput("Add Telegram authorization with backend, frontend, tests, and docs"), TaskContext("demo", ".", "main"))
    advisory_context = {
        "local_llm": {
            "decomposition": {
                "status": "model",
                "layers": [
                    {"name": "intake", "objective": "Normalize the request", "capability": "plan", "task_type": "plan", "dependencies": []},
                    {"name": "implementation", "objective": "Implement backend and frontend changes", "capability": "code", "task_type": "code", "dependencies": ["intake"]},
                    {"name": "verification", "objective": "Prepare tests and checks", "capability": "test", "task_type": "test", "dependencies": ["implementation"]},
                ],
            }
        }
    }

    plan = TaskDecomposer().decompose(task, advisory_context=advisory_context)

    assert [atomic.draft_layer for atomic in plan.atomic_tasks] == ["intake", "implementation", "verification"]
    assert plan.draft_layers[0]["name"] == "intake"
    assert plan.atomic_tasks[1].dependencies == [plan.atomic_tasks[0].task_id]


def test_orchestrator_create_execution_plan_uses_local_llm_advisory(monkeypatch):
    from ai_bridge.core.models import ExecutionPlan, Task, TaskContext, TaskInput, TaskType

    orchestrator = Orchestrator()
    task = Task(TaskType.PLAN, TaskInput("Add Telegram authorization with backend, frontend, tests, and docs"), TaskContext("demo", ".", "main"))

    captured: dict[str, object] = {}

    def fake_decompose(task_obj, advisory_context=None):
        captured["advisory_context"] = advisory_context
        return ExecutionPlan(root_task_id=task_obj.task_id, atomic_tasks=[task_obj], draft_layers=[])

    monkeypatch.setattr(orchestrator.decomposer, "decompose", fake_decompose)
    orchestrator.module_manager = SimpleNamespace(get_module=lambda name: None)
    monkeypatch.setattr(orchestrator, "_build_decomposition_advisory", lambda task_obj: {"local_llm": {"decomposition": {"layers": [{"name": "intake", "objective": "Normalize request", "capability": "plan", "task_type": "plan", "dependencies": []}]}}})

    plan = orchestrator.create_execution_plan(task)

    assert len(plan.atomic_tasks) == 1
    assert "local_llm" in captured["advisory_context"]
    assert captured["advisory_context"]["local_llm"]["decomposition"]["layers"][0]["name"] == "intake"



def test_api_bridge_full_health_snapshot_contains_providers_and_agents():
    from ai_bridge.core.api_bridge_module import APIBridgeModule

    class _Health:
        def __init__(self, payload):
            self._payload = payload

        def as_dict(self):
            return self._payload

    class _Healthcheck:
        def check_providers(self):
            return {
                "gemini": _Health({"provider": "gemini", "status": "healthy"}),
                "mistral": _Health({"provider": "mistral", "status": "healthy"}),
            }

        def check_all(self):
            return [
                _Health({"agent_id": "codex-main", "status": "ready"}),
                _Health({"agent_id": "tester-1", "status": "ready"}),
            ]

    class _ModuleManager:
        def finalize(self):
            return {"sourcecraft": {"status": "ready"}}

    class _Registry:
        def list_agents(self):
            return [1, 2]

    class _API:
        def __init__(self):
            self.healthcheck = _Healthcheck()
            self.registry = _Registry()
            self.module_manager = _ModuleManager()
            self.sourcecraft = SourceCraftModule()
            self.sourcecraft.on_load(_FakeAPI())

        def get_context(self, key):
            return getattr(self, key, None)

        def get_module(self, name):
            return self.sourcecraft if name == "sourcecraft" else None

    module = APIBridgeModule()
    module._api = _API()
    snapshot = module._health_full_snapshot()

    assert snapshot["status"] == "ok"
    assert snapshot["overall_ok"] is True
    assert snapshot["summary"]["provider_count"] == 2
    assert snapshot["summary"]["agent_count"] == 2
    assert snapshot["sourcecraft"]["role"]["name"] == "sourcecraft"
    assert snapshot["modules"]["sourcecraft"]["status"] == "ready"
