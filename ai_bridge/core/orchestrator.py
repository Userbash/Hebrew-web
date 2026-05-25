from __future__ import annotations

from ai_bridge.agents.base_agent import BaseAgent

from .agent_autoscaler import AgentAutoscaler
from .agent_lifecycle import AgentLifecycleManager
from .agent_registry import AgentRegistry
from .feedback_loop import FeedbackLoop
from .healthcheck import HealthChecker
from .host_bridge import HostBridge
from .kpi import KPIEvaluator
from .load_balancer import LoadBalancer
from .metrics import MetricsCollector
from .message_bus import MessageBus
from .model_selector import ModelSelector
from .models import AgentResult, ExecutionPlan, Task, TaskStatus
from .orchestration_config import OrchestrationConfig
from .quality_analyzer import QualityAnalyzer
from .security_gate import SecurityGate
from .result_merger import ResultMerger
from .smart_scheduler import SmartScheduler
from .session_memory import MemoryScope, SessionMemory
from .availability import ModelAvailability
from .ai_activity_module import AIActivityModule
from .kernel_module_manager import KernelModuleManager


TIMEOUT_ERROR_TYPES = {"tcp_timeout", "api_timeout", "sdk_hang"}
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
        self.orchestration_config = OrchestrationConfig.from_env()
        self.scheduler = SmartScheduler(self.registry)
        self.message_bus = MessageBus()
        self.healthcheck = HealthChecker(self.registry)
        self.availability = ModelAvailability()
        self.feedback = FeedbackLoop(retry_limit=retry_limit)
        self.metrics = MetricsCollector()
        self.kpi = KPIEvaluator()
        self.quality = QualityAnalyzer()
        self.merger = ResultMerger()
        self.console = UserConsole()
        self.security_gate = SecurityGate()
        self.host_bridge = HostBridge()
        self.session_memory = SessionMemory()
        self.module_manager = KernelModuleManager()
        self.module_manager.register(AIActivityModule())
        self.module_manager.load("ai_activity")
        self.local_agents: dict[str, BaseAgent] = {}
        self.results: dict[str, AgentResult] = {}
        self.live_trace_rows: list[dict[str, object]] = []

    def attach_local_agent(self, agent_id: str, agent: BaseAgent, agent_type: str = "custom", critical: bool = False, model_name: str = "local-small", provider: str = "local") -> None:
        self.local_agents[agent_id] = agent
        agent.set_host_bridge(self.host_bridge)
        if not self.registry.get(agent_id):
            self.registry.register(agent_id, agent_type, f"local://{agent_id}", agent.capabilities, critical=critical, model_name=model_name, provider=provider)
            self.metrics.register_agent(self.registry.get(agent_id))  # type: ignore[arg-type]

    def load_kernel_module(self, name: str) -> None:
        self.module_manager.load(name)

    def unload_kernel_module(self, name: str) -> None:
        self.module_manager.unload(name)

    def loaded_kernel_modules(self) -> list[str]:
        return self.module_manager.loaded_modules()

    def create_execution_plan(self, task: Task) -> ExecutionPlan:
        self.console.emit("PLAN", "Задача проанализирована")
        plan = self.decomposer.decompose(task)
        self.console.emit("PLAN", f"Создано атомарных задач: {len(plan.atomic_tasks)}")
        return plan

    def _load_memory_context(self, task: Task, agent_id: str) -> dict[str, object]:
        scope_name = (task.memory_scope or "task").lower()
        scope = MemoryScope.TASK
        if scope_name == "session":
            scope = MemoryScope.SESSION
        elif scope_name == "agent":
            scope = MemoryScope.AGENT
        elif scope_name == "capability":
            scope = MemoryScope.CAPABILITY

        if scope == MemoryScope.SESSION:
            identifier = task.session_id or "default"
        elif scope == MemoryScope.AGENT:
            identifier = agent_id
        elif scope == MemoryScope.CAPABILITY:
            identifier = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
        else:
            identifier = task.task_id

        context: dict[str, object] = {}
        if task.cache_policy == "write_only":
            return context
        for key in task.memory_keys:
            value = self.session_memory.get(scope, identifier, key)
            if value is not None:
                context[key] = value
        return context

    def _find_fallback_agent(self, capability: str, providers: list[str], exclude: set[str]) -> str | None:
        for provider in providers:
            for record in self.registry.list_agents():
                if record.id in exclude:
                    continue
                if record.provider != provider:
                    continue
                if capability not in record.capabilities:
                    continue
                if record.status.value in {"offline", "disabled", "failed"}:
                    continue
                if record.id in self.local_agents:
                    return record.id
        return None

    def run_task(self, task: Task) -> AgentResult:
        capability = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]

        choice = self.model_selector.select(task)
        self.console.emit(
            "MODEL_SELECTION",
            f"task_id={task.task_id} task_type={task.type.value} detected_keywords={choice.detected_keywords or []} "
            f"matched_high_risk_rules={choice.matched_high_risk_rules or []} "
            f"matched_low_risk_exemptions={choice.matched_low_risk_exemptions or []} "
            f"final_complexity={choice.complexity.value} selected_provider={choice.provider} selected_model={choice.model_name} "
            f"secondary_review={choice.requires_secondary_review} reason={choice.reason}",
        )

        module_context: dict[str, object] = {
            "selected_provider": choice.provider,
            "selected_model": choice.model_name,
            "reason": choice.reason,
        }
        self.module_manager.before_task(task, module_context)

        self.autoscaler.ensure_capacity(capability)
        decision = self.scheduler.schedule(task)
        if decision.requires_orchestrator:
            self.console.emit("SCHEDULER", f"Orchestrator route: {decision.reason}")
        else:
            self.console.emit("SCHEDULER", f"P2P route allowed: {decision.reason}")

        acceptance = self.router.route(task)
        if acceptance.status == TaskStatus.REJECTED or not acceptance.assigned_agent:
            self.console.emit("ROUTING", acceptance.message)
            self.live_trace_rows.append(
                {
                    "task_id": task.task_id,
                    "task_type": task.type.value,
                    "detected_keywords": choice.detected_keywords or [],
                    "matched_high_risk_rules": choice.matched_high_risk_rules or [],
                    "matched_low_risk_exemptions": choice.matched_low_risk_exemptions or [],
                    "final_complexity": choice.complexity.value,
                    "selected_provider": choice.provider,
                    "selected_model": choice.model_name,
                    "router_agent": None,
                    "router_provider": None,
                    "fallback": False,
                    "secondary_review": choice.requires_secondary_review,
                    "reason": acceptance.message,
                }
            )
            failed_result = AgentResult(task.task_id, "orchestrator", TaskStatus.FAILED, {"summary": acceptance.message, "files_changed": [], "commands_run": [], "test_results": [], "diff": ""}, 0.0, [acceptance.message], [])
            self.module_manager.after_task(task, failed_result, module_context)
            return failed_result

        agent_id = acceptance.assigned_agent
        agent_record = self.registry.get(agent_id)
        fallback = bool(choice.provider != "openai" and agent_record and agent_record.provider == "openai")

        module_context["agent_id"] = agent_id
        module_context["provider"] = agent_record.provider if agent_record else choice.provider
        module_context["model"] = agent_record.model_name if agent_record else choice.model_name
        module_context["fallback"] = fallback

        self.console.emit(
            "ROUTING",
            f"task_id={task.task_id} router_agent={agent_id} router_provider={agent_record.provider if agent_record else '-'} "
            f"fallback={fallback} secondary_review={choice.requires_secondary_review}",
        )

        # Pre-flight availability check
        provider = agent_record.provider if agent_record else choice.provider
        if not self.availability.is_provider_ready(provider):
            self.console.emit("EXECUTION", f"Provider {provider} is not ready. Skipping execution.")
            failed_result = AgentResult(task.task_id, agent_id, TaskStatus.FAILED, {"summary": f"Provider {provider} unreachable or auth failed", "files_changed": [], "commands_run": [], "test_results": [], "diff": ""}, 0.0, [f"Provider {provider} unavailable"], [])
            self.module_manager.after_task(task, failed_result, module_context)
            return failed_result

        self.live_trace_rows.append(
            {
                "task_id": task.task_id,
                "task_type": task.type.value,
                "detected_keywords": choice.detected_keywords or [],
                "matched_high_risk_rules": choice.matched_high_risk_rules or [],
                "matched_low_risk_exemptions": choice.matched_low_risk_exemptions or [],
                "final_complexity": choice.complexity.value,
                "selected_provider": choice.provider,
                "selected_model": choice.model_name,
                "router_agent": agent_id,
                "router_provider": agent_record.provider if agent_record else None,
                "fallback": fallback,
                "secondary_review": choice.requires_secondary_review,
                "reason": choice.reason,
            }
        )

        if agent_record:
            agent_record.metrics.queue_depth = max(0, agent_record.metrics.queue_depth - 1)
            if task.assigned_model:
                agent_record.metrics.model_name = task.assigned_model
            self.lifecycle.mark_busy(agent_record, task)
            self.console.emit("EXECUTION", f"task_id={task.task_id} agent={agent_id} stage=start")
            self.console.agent_status(agent_record, task, progress=35, stage="выполняет задачу")

        try:
            agent = self.local_agents.get(agent_id)
            if not agent:
                failed_result = AgentResult(task.task_id, agent_id, TaskStatus.FAILED, {"summary": "No local executor for routed agent", "files_changed": [], "commands_run": [], "test_results": [], "diff": ""}, 0.0, ["No local executor"], [])
                self.module_manager.after_task(task, failed_result, module_context)
                return failed_result
            memory_context = self._load_memory_context(task, agent_id)
            result = agent.run(task, memory_context=memory_context)

            is_gemini = bool(agent_record and agent_record.provider in {"google", "gemini", "gemini-cli"})
            result_errors = " ".join(result.errors or [])
            classified = ""
            if result_errors:
                try:
                    from .external_ai_bridge import ExternalAIBridge
                    classified = ExternalAIBridge.classify_error(result_errors)
                except Exception:
                    classified = ""

            if result.status == TaskStatus.FAILED and is_gemini and classified in TIMEOUT_ERROR_TYPES:
                fallback_chain = ["mistral", "local"]
                fallback_agent_id = self._find_fallback_agent(capability, fallback_chain, exclude={agent_id})
                if fallback_agent_id:
                    self.console.emit("FALLBACK", f"task_id={task.task_id} from={agent_id} to={fallback_agent_id} reason={classified}")
                    fallback_agent = self.local_agents.get(fallback_agent_id)
                    if fallback_agent:
                        result = fallback_agent.run(task, memory_context=memory_context)
            quality = self.quality.analyze(task, result)
            if agent_record:
                agent_record.metrics.quality_score = quality.score
                self.metrics.record_result(agent_record, result)
                self.kpi.apply_priority_policy(agent_record)
            self.results[task.task_id] = result
            if task.cache_policy in {"write_only", "read_write"}:
                scope_name = (task.memory_scope or "task").lower()
                scope = MemoryScope.TASK
                if scope_name == "session":
                    scope = MemoryScope.SESSION
                elif scope_name == "agent":
                    scope = MemoryScope.AGENT
                elif scope_name == "capability":
                    scope = MemoryScope.CAPABILITY

                if scope == MemoryScope.SESSION:
                    identifier = task.session_id or "default"
                elif scope == MemoryScope.AGENT:
                    identifier = agent_id
                elif scope == MemoryScope.CAPABILITY:
                    identifier = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
                else:
                    identifier = task.task_id

                self.session_memory.set(scope, identifier, "last_result", result.as_dict(), ttl_sec=task.memory_ttl_sec)
                self.session_memory.set(scope, identifier, "last_summary", result.output.get("summary", ""), ttl_sec=task.memory_ttl_sec)
            self.console.emit("EXECUTION", f"task_id={task.task_id} agent={agent_id} status={result.status.value}")

            resolved_record = self.registry.get(result.agent_id)
            if resolved_record:
                module_context["agent_id"] = result.agent_id
                module_context["provider"] = resolved_record.provider
                module_context["model"] = resolved_record.model_name
            self.module_manager.after_task(task, result, module_context)

            if choice.requires_secondary_review:
                self.console.emit(
                    "SECONDARY_REVIEW",
                    f"task_id={task.task_id} enabled=true reason={choice.reason}",
                )

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
        self.live_trace_rows = []
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
                    module_state = self.module_manager.finalize()
                    return {"status": "failed", "merged": merged, "results": [r.as_dict() for r in final_results], "metrics": self.metrics.snapshot(), "console": self.console.events, "live_trace": self.live_trace_rows, "scheduler": [decision.as_dict() for decision in self.scheduler.decisions], "kernel_modules": self.module_manager.loaded_modules(), "module_state": module_state, "ai_activity": module_state.get("ai_activity", {})}
                completed.add(task.task_id)
                pending.pop(task.task_id)
        merged = self.merger.merge(final_results)
        self.console.emit("DONE", "Все критерии выполнены")
        module_state = self.module_manager.finalize()
        return {"status": "done", "merged": merged, "results": [r.as_dict() for r in final_results], "metrics": self.metrics.snapshot(), "console": self.console.events, "live_trace": self.live_trace_rows, "disabled_agents": self.autoscaler.disabled_agents, "enabled_agents": self.autoscaler.enabled_agents, "scheduler": [decision.as_dict() for decision in self.scheduler.decisions], "kernel_modules": self.module_manager.loaded_modules(), "module_state": module_state, "ai_activity": module_state.get("ai_activity", {})}
