from ai_bridge.core.agent_registry import AgentRegistry
from ai_bridge.core.load_balancer import LoadBalancer
from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.task_router import TaskRouter


def test_register_agent_and_route_by_capability():
    registry = AgentRegistry()
    registry.register("tester-1", "tester", "local://tester", ["test", "ci"])
    router = TaskRouter(registry, LoadBalancer())
    task = Task(TaskType.TEST, TaskInput("run tests"), TaskContext("p", ".", "main"))

    accepted = router.route(task)

    assert accepted.assigned_agent == "tester-1"
    assert accepted.status.value == "accepted"


def test_balancer_avoids_high_load_agent():
    registry = AgentRegistry()
    busy = registry.register("busy", "tester", "local://busy", ["test"], limits={"max_active_tasks": 1})
    idle = registry.register("idle", "tester", "local://idle", ["test"], limits={"max_active_tasks": 5})
    busy.metrics.active_tasks = 3
    idle.metrics.active_tasks = 0

    chosen = LoadBalancer().choose(registry.list_agents(), "test")

    assert chosen is idle
