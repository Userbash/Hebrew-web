from __future__ import annotations

from ai_bridge.agents.base_agent import BaseAgent

from .agent_autoscaler import AgentAutoscaler
from .agent_lifecycle import AgentLifecycleManager
from .agent_registry import AgentRegistry
from .feedback_loop import FeedbackLoop
from .healthcheck import HealthChecker
from .kpi import KPIEvaluator
from .load_balancer import LoadBalancer
from .metrics import MetricsCollector
from .model_selector import ModelSelector
from .models import AgentResult, ExecutionPlan, Task, TaskStatus
from .quality_analyzer import QualityAnalyzer
from .result_merger import ResultMerger
from .task_decomposer import TaskDecomposer
from .task_router import CAPABILITY_BY_TASK_TYPE, TaskRouter
from .user_console import UserConsole


class Orchestrator:
    def __init__(self, registry: AgentRegistry | None = None, retry_limit: int = 3, idle_shutdown_sec: int = 900) -> None:
        self.registry = registry or AgentRegistry()
        self.lifecycle = AgentLifecycleManager(idle_shutdown_sec=idle_shutdown_sec)
        self.autoscaler = AgentAutoscaler(self.registry, self.lifecycle)
        self.load_balancer = LoadBalancer()
        self.model_selector = ModelSelector()
        self.decomposer = TaskDecomposer(self.model_selector)
        self.router = TaskRouter(self.registry, self.load_balancer)
        self.healthcheck = HealthChecker(self.registry)
        self.feedback = FeedbackLoop(retry_limit=retry_limit)
        self.metrics = MetricsCollector()
        self.kpi = KPIEvaluator()
        self.quality = QualityAnalyzer()
        self.merger = ResultMerger()
        self.console = UserConsole()
        self.local_agents: dict[str, BaseAgent] = {}
        self.results: dict[str, AgentResult] = {}

    def attach_local_agent(self, agent_id: str, agent: BaseAgent, agent_type: str = "custom", critical: bool = False, model_name: str = "local-small", provider: str = "local") -> None:
        self.local_agents[agent_id] = agent
        if not self.registry.get(agent_id):
            self.registry.register(agent_id, agent_type, f"local://{agent_id}", agent.capabilities, critical=critical, model_name=model_name, provider=provider)
            self.metrics.register_agent(self.registry.get(agent_id))  # type: ignore[arg-type]

    def create_execution_plan(self, task: Task) -> ExecutionPlan:
        self.console.emit("PLAN", "Задача проанализирована")
        plan = self.decomposer.decompose(task)
        self.console.emit("PLAN", f"Создано атомарных задач: {len(plan.atomic_tasks)}")
        return plan

    def run_task(self, task: Task) -> AgentResult:
        capability = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
        self.autoscaler.ensure_capacity(capability)
        acceptance = self.router.route(task)
        if acceptance.status == TaskStatus.REJECTED or not acceptance.assigned_agent:
            self.console.emit("ROUTING", acceptance.message)
            return AgentResult(task.task_id, "orchestrator", TaskStatus.FAILED, {"summary": acceptance.message, "files_changed": [], "commands_run": [], "test_results": [], "diff": ""}, 0.0, [acceptance.message], [])

        agent_id = acceptance.assigned_agent
        agent_record = self.registry.get(agent_id)
        if agent_record:
            agent_record.metrics.queue_depth = max(0, agent_record.metrics.queue_depth - 1)
            if task.assigned_model:
                agent_record.metrics.model_name = task.assigned_model
            self.lifecycle.mark_busy(agent_record, task)
            self.console.emit("ROUTING", f"{task.type.value} передан агенту {agent_id}")
            self.console.agent_status(agent_record, task, progress=35, stage="выполняет задачу")
        try:
            agent = self.local_agents.get(agent_id)
            if not agent:
                return AgentResult(task.task_id, agent_id, TaskStatus.FAILED, {"summary": "No local executor for routed agent", "files_changed": [], "commands_run": [], "test_results": [], "diff": ""}, 0.0, ["No local executor"], [])
            result = agent.run(task)
            quality = self.quality.analyze(task, result)
            if agent_record:
                agent_record.metrics.quality_score = quality.score
                self.metrics.record_result(agent_record, result)
                self.kpi.apply_priority_policy(agent_record)
            self.results[task.task_id] = result
            if not quality.passed:
                self.console.emit("REVIEW", f"Качество ниже порога: {', '.join(quality.issues)}")
            ok, fix_task = self.feedback.evaluate(task, result)
            if not ok and fix_task:
                self.console.emit("FIX", "Найдены ошибки, создана задача исправления")
                fix_result = self.run_task(fix_task)
                if fix_result.status == TaskStatus.DONE:
                    return AgentResult(task.task_id, fix_result.agent_id, TaskStatus.DONE, fix_result.output, min(0.8, fix_result.confidence), fix_result.errors, fix_result.next_recommendations)
            return result
        finally:
            if agent_record:
                self.lifecycle.mark_idle(agent_record)
                self.autoscaler.scale_down_idle()

    def run(self, root_task: Task) -> dict:
        self.console.emit("AGENTS", f"Найдено агентов: {len(self.registry.list_agents())}, доступно: {len(self.registry.ready_agents())}")
        self.healthcheck.check_all()
        plan = self.create_execution_plan(root_task)
        completed: set[str] = set()
        pending = {task.task_id: task for task in plan.atomic_tasks}
        final_results: list[AgentResult] = []

        while pending:
            ready = [task for task in pending.values() if all(dep in completed for dep in task.dependencies)]
            if not ready:
                raise RuntimeError("Task graph has unresolved dependencies")
            for task in ready:
                result = self.run_task(task)
                final_results.append(result)
                if result.status != TaskStatus.DONE:
                    merged = self.merger.merge(final_results)
                    return {"status": "failed", "merged": merged, "results": [r.as_dict() for r in final_results], "metrics": self.metrics.snapshot(), "console": self.console.events}
                completed.add(task.task_id)
                pending.pop(task.task_id)
        merged = self.merger.merge(final_results)
        self.console.emit("DONE", "Все критерии выполнены")
        return {"status": "done", "merged": merged, "results": [r.as_dict() for r in final_results], "metrics": self.metrics.snapshot(), "console": self.console.events, "disabled_agents": self.autoscaler.disabled_agents, "enabled_agents": self.autoscaler.enabled_agents}
