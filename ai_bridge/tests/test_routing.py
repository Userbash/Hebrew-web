from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.load_balancer import LoadBalancer
from ai_bridge.core.models import AgentStatus, Priority, Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.task_router import TaskRouter
from ai_bridge.core.orchestrator import Orchestrator


def test_register_agent_and_route_by_capability():
    registry = AgentRegistry()
    registry.register("tester-1", "tester", "local://tester", ["test", "ci"])
    router = TaskRouter(registry, LoadBalancer())
    task = Task(TaskType.TEST, TaskInput("run tests"), TaskContext("p", ".", "main"))

    accepted = router.route(task)

    assert accepted.assigned_agent == "tester-1"
    assert accepted.status.value == "accepted"


def test_sourcecraft_task_routes_to_orchestrator_when_no_dedicated_agent():
    registry = AgentRegistry()
    registry.register("codex-main", "codex", "local://codex", ["code", "fix"])
    router = TaskRouter(registry, LoadBalancer())
    task = Task(TaskType.CODE, TaskInput("Prepare SourceCraft release notes and PR flow for repo status"), TaskContext("p", ".", "main"))
    task.required_capability = "sourcecraft"

    accepted = router.route(task)

    assert accepted.status.value == "accepted"
    assert accepted.assigned_agent == "orchestrator"


def test_balancer_avoids_high_load_agent():
    registry = AgentRegistry()
    busy = registry.register("busy", "tester", "local://busy", ["test"], limits={"max_active_tasks": 1})
    idle = registry.register("idle", "tester", "local://idle", ["test"], limits={"max_active_tasks": 5})
    busy.metrics.active_tasks = 3
    idle.metrics.active_tasks = 0

    chosen = LoadBalancer().choose(registry.list_agents(), "test")

    assert chosen is idle


def test_router_excludes_unroutable_agent_statuses():
    for status in (AgentStatus.FAILED, AgentStatus.OFFLINE, AgentStatus.DISABLED, AgentStatus.OVERLOADED):
        registry = AgentRegistry()
        record = registry.register(f"agent-{status.value}", "tester", f"local://{status.value}", ["test"])
        record.status = status
        record.metrics.status = status
        router = TaskRouter(registry, LoadBalancer())
        task = Task(TaskType.TEST, TaskInput("run tests"), TaskContext("p", ".", "main"))

        accepted = router.route(task)

        assert accepted.status.value == "rejected"
        assert accepted.assigned_agent is None


def test_busy_agent_only_accepts_low_priority_tasks():
    registry = AgentRegistry()
    record = registry.register("busy", "docs", "local://busy", ["docs"])
    record.status = AgentStatus.BUSY
    record.metrics.status = AgentStatus.BUSY
    router = TaskRouter(registry, LoadBalancer())

    normal_task = Task(TaskType.DOCS, TaskInput("write docs"), TaskContext("p", ".", "main"), priority=Priority.NORMAL)
    low_task = Task(TaskType.DOCS, TaskInput("write docs"), TaskContext("p", ".", "main"), priority=Priority.LOW)

    rejected = router.route(normal_task)
    accepted = router.route(low_task)

    assert rejected.status.value == "rejected"
    assert rejected.assigned_agent is None
    assert accepted.status.value == "accepted"
    assert accepted.assigned_agent == "busy"


def test_orchestrator_provider_preference_uses_agent_filtering():
    registry = AgentRegistry()
    overloaded = registry.register("overloaded", "docs", "local://overloaded", ["docs"], provider="local")
    overloaded.status = AgentStatus.OVERLOADED
    overloaded.metrics.status = AgentStatus.OVERLOADED
    busy = registry.register("busy", "docs", "local://busy", ["docs"], provider="local")
    busy.status = AgentStatus.BUSY
    busy.metrics.status = AgentStatus.BUSY

    orchestrator = object.__new__(Orchestrator)
    orchestrator.registry = registry
    orchestrator.local_agents = {"overloaded": object(), "busy": object()}

    normal_choice = orchestrator._select_agent_by_provider_preference("docs", ["local"], priority=Priority.NORMAL)
    low_choice = orchestrator._select_agent_by_provider_preference("docs", ["local"], priority=Priority.LOW)

    assert normal_choice is None
    assert low_choice == "busy"


def test_router_excludes_agents_over_capacity_before_scoring():
    registry = AgentRegistry()
    overloaded = registry.register("calculated-overloaded", "tester", "local://overloaded", ["test"], limits={"max_active_tasks": 1})
    ready = registry.register("ready", "tester", "local://ready", ["test"], limits={"max_active_tasks": 5})
    overloaded.metrics.active_tasks = 2
    router = TaskRouter(registry, LoadBalancer())
    task = Task(TaskType.TEST, TaskInput("run tests"), TaskContext("p", ".", "main"))

    accepted = router.route(task)

    assert overloaded.status == AgentStatus.OVERLOADED
    assert accepted.status.value == "accepted"
    assert accepted.assigned_agent == "ready"
