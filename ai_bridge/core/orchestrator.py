from __future__ import annotations
import asyncio
from typing import Any

from ai_bridge.agents.base_agent import BaseAgent

from .agent_factory import AgentFactory
from .agent_registry import AgentRegistry
from .feedback_loop import FeedbackLoop
from .healthcheck import HealthChecker
from .host_bridge import HostBridge
from .kpi import KPIEvaluator
from .load_balancer import LoadBalancer
from .metrics import MetricsCollector
from .message_bus import MessageBus
from .model_selector import ModelSelector
from .models import AgentResult, ExecutionPlan, Priority, Task, TaskAcceptance, TaskStatus
from .orchestration_config import OrchestrationConfig
from .quality_analyzer import QualityAnalyzer
from .security_gate import SecurityGate
from .result_merger import ResultMerger
from .smart_scheduler import SmartScheduler
from .session_memory import MemoryScope, SessionMemory
from .availability import ModelAvailability
from .ai_activity_module import AIActivityModule
from .api_bridge_module import APIBridgeModule
from .smart_decomposer_module import SmartDecomposerModule
from .prompt_optimizer_module import PromptOptimizerModule
from .chat_bus import ChatBusModule
from .trigger_dispatcher import TriggerDispatcherModule
from .json_themes_module import JSONThemesModule
from .unified_vfs import UnifiedVFSModule
from .kernel_module_manager import KernelModuleManager
from .orchestrator_control_module import OrchestratorControlModule
from .model_usage_module import ModelUsageModule
from .provider_budget_router import ProviderBudgetRouter
from .cold_boot_module import ColdBootModule


TIMEOUT_ERROR_TYPES = {"tcp_timeout", "api_timeout", "sdk_hang"}
from .task_decomposer import TaskDecomposer
from .task_router import CAPABILITY_BY_TASK_TYPE, TaskRouter
from .user_console import UserConsole


class Orchestrator:
    def get_context(self, key: str) -> Any:
        return getattr(self, key, None)

    def emit_event(self, event_name: str, payload: dict[str, Any]) -> None:
        self.console.emit(event_name, str(payload))

    def query_state(self, module_name: str, key: str) -> Any:
        return self.module_manager.finalize().get(module_name, {}).get(key)

    def query_module_state(self, module_name: str, key: str) -> Any:
        return self.query_state(module_name, key)

    def get_memory(self) -> SessionMemory:
        return self.session_memory

    def log(self, level: str, message: str) -> None:
        getattr(self.console, level, self.console.emit)(f"KERNEL:{level.upper()}", message)

    def get_module(self, name: str) -> Any:
        return self.module_manager.get_module(name)

    def load_module(self, name: str) -> None:
        self.module_manager.load(name)

    def unload_module(self, name: str) -> None:
        self.module_manager.unload(name)

    def __init__(self, registry: AgentRegistry | None = None, retry_limit: int = 3, idle_shutdown_sec: int = 900) -> None:
        self.local_agents: dict[str, BaseAgent] = {}
        self.results: dict[str, AgentResult] = {}
        self.live_trace_rows: list[dict[str, object]] = []
        
        components = AgentFactory.build(registry=registry, retry_limit=retry_limit, idle_shutdown_sec=idle_shutdown_sec)
        
        self.registry = components.registry
        self.lifecycle = components.lifecycle
        self.autoscaler = components.autoscaler
        self.load_balancer = components.load_balancer
        self.model_selector = components.model_selector
        self.decomposer = components.decomposer
        self.router = components.router
        self.orchestration_config = components.orchestration_config
        self.scheduler = components.scheduler
        self.message_bus = components.message_bus
        self.healthcheck = components.healthcheck
        self.availability = ModelAvailability()
        self.feedback = components.feedback
        self.metrics = components.metrics
        self.kpi = components.kpi
        self.quality = components.quality
        self.merger = components.merger
        self.console = components.console
        self.security_gate = components.security_gate
        self.host_bridge = components.host_bridge
        self.session_memory = components.session_memory
        self.memory_consolidator = components.memory_consolidator
        self.provider_budget_router = ProviderBudgetRouter()
        
        self.module_manager = KernelModuleManager()
        self.module_manager.set_api(self)
        self.module_manager.register(AIActivityModule())
        self.module_manager.register(OrchestratorControlModule())
        self.module_manager.register(ModelUsageModule())
        self.module_manager.register(APIBridgeModule())
        self.module_manager.register(SmartDecomposerModule())
        self.module_manager.register(PromptOptimizerModule())
        self.module_manager.register(ChatBusModule())
        self.module_manager.register(TriggerDispatcherModule())
        self.module_manager.register(JSONThemesModule())
        self.module_manager.register(UnifiedVFSModule())
        self.module_manager.register(ColdBootModule())
        
        self.module_manager.load("ai_activity")
        self.module_manager.load("orchestrator_control")
        self.module_manager.load("model_usage")
        self.module_manager.load("api_bridge")
        self.module_manager.load("smart_decomposer")
        self.module_manager.load("prompt_optimizer")
        self.module_manager.load("chat_bus")
        self.module_manager.load("trigger_dispatcher")
        self.module_manager.load("json_themes")
        self.module_manager.load("unified_vfs")
        self.module_manager.load("cold_boot")

    def _init_original(self, registry: AgentRegistry | None = None, retry_limit: int = 3, idle_shutdown_sec: int = 900) -> None:
        self.local_agents = {}
        self.results = {}
        self.live_trace_rows = []

        components = AgentFactory.build(registry=registry, retry_limit=retry_limit, idle_shutdown_sec=idle_shutdown_sec)

        self.registry = components.registry
        self.lifecycle = components.lifecycle
        self.autoscaler = components.autoscaler
        self.load_balancer = components.load_balancer
        self.model_selector = components.model_selector
        self.decomposer = components.decomposer
        self.router = components.router
        self.orchestration_config = components.orchestration_config
        self.scheduler = components.scheduler
        self.message_bus = components.message_bus
        self.healthcheck = components.healthcheck
        self.availability = ModelAvailability()
        self.feedback = components.feedback
        self.metrics = components.metrics
        self.kpi = components.kpi
        self.quality = components.quality
        self.merger = components.merger
        self.console = components.console
        self.security_gate = components.security_gate
        self.host_bridge = components.host_bridge
        self.session_memory = components.session_memory
        self.provider_budget_router = ProviderBudgetRouter()

        self.module_manager = KernelModuleManager()
        self.module_manager.set_api(self)
        self.module_manager.register(AIActivityModule())
        self.module_manager.register(OrchestratorControlModule())
        self.module_manager.register(ModelUsageModule())
        self.module_manager.register(APIBridgeModule())
        self.module_manager.register(SmartDecomposerModule())
        self.module_manager.register(PromptOptimizerModule())
        self.module_manager.register(ChatBusModule())
        self.module_manager.register(TriggerDispatcherModule())
        self.module_manager.register(ColdBootModule())
        self.module_manager.load("ai_activity")
        self.module_manager.load("orchestrator_control")
        self.module_manager.load("model_usage")
        self.module_manager.load("api_bridge")
        self.module_manager.load("smart_decomposer")
        self.module_manager.load("prompt_optimizer")
        self.module_manager.load("chat_bus")
        self.module_manager.load("trigger_dispatcher")
        self.module_manager.load("cold_boot")
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

    def _control_module(self) -> OrchestratorControlModule | None:
        module = self.module_manager.get_module("orchestrator_control")
        if isinstance(module, OrchestratorControlModule):
            return module
        return None

    def submit_user_task(self, payload: object, source: str = "user_input") -> dict[str, object]:
        from .task_submission_api import create_standard_task, normalize_user_payload

        normalized = normalize_user_payload(payload)
        task = create_standard_task(normalized)
        control = self._control_module()
        if control is not None:
            control.register_submission(task, source=source)
        return self.run(task)

    def monitoring_snapshot(self) -> dict[str, object]:
        control = self._control_module()
        if control is None:
            return {"source_of_truth": "orchestrator", "status": "control_module_not_loaded"}
        return control.finalize()

    @staticmethod
    def _normalize_provider(provider: str) -> str:
        p = provider.strip().lower()
        if p in {"google", "gemini", "gemini-cli"}:
            return "google"
        return p

    def _select_agent_by_provider_preference(self, capability: str, providers: list[str], exclude: set[str] | None = None) -> str | None:
        skip = exclude or set()
        normalized = [self._normalize_provider(p) for p in providers]
        for provider in normalized:
            for record in self.registry.list_agents():
                if record.id in skip:
                    continue
                if capability not in record.capabilities:
                    continue
                if self._normalize_provider(record.provider) != provider:
                    continue
                if record.status.value in {"offline", "disabled", "failed"}:
                    continue
                if record.id in self.local_agents:
                    return record.id
        return None


    def create_execution_plan(self, task: Task) -> ExecutionPlan:
        self.console.emit("PLAN", "Задача проанализирована")

        # Try smart decomposition first
        smart_decomp = self.module_manager.get_module("smart_decomposer")
        if isinstance(smart_decomp, SmartDecomposerModule):
            plan = smart_decomp.decompose_task(task)
            if plan:
                self.console.emit("PLAN", f"Умная декомпозиция: создано {len(plan.atomic_tasks)} задач")
                return plan

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
            normalized = key.lower()
            if "thought" in normalized or normalized.endswith(":errors") or normalized == "errors":
                continue
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
        self.log("info", f"[PRE-FLIGHT] Verifying readiness for task {task.task_id}")
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

        preferred_providers = self.provider_budget_router.preferred_providers(task, choice)
        preferred_agent_id = self._select_agent_by_provider_preference(capability, preferred_providers)
        if preferred_agent_id:
            acceptance = TaskAcceptance(task.task_id, TaskStatus.ACCEPTED, preferred_agent_id, self.router.estimate_complexity(task), "Task accepted (provider budget routing)")
        else:
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
        selected_provider_norm = self._normalize_provider(choice.provider)
        routed_provider_norm = self._normalize_provider(agent_record.provider if agent_record else choice.provider)
        fallback = bool(selected_provider_norm != routed_provider_norm)

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
        provider = self._normalize_provider(agent_record.provider if agent_record else choice.provider)
        if not self.availability.is_provider_ready(provider):
            self.console.emit("EXECUTION", f"Provider {provider} is not ready. Trying fallback providers.")
            fallback_chain = self.provider_budget_router.preferred_providers(task, choice)
            selected_fallback_id = None
            selected_fallback_record = None

            for candidate_provider in fallback_chain:
                fallback_agent_id = self._select_agent_by_provider_preference(capability, [candidate_provider], exclude={agent_id})
                if not fallback_agent_id:
                    continue
                fallback_record = self.registry.get(fallback_agent_id)
                fallback_provider = self._normalize_provider(fallback_record.provider if fallback_record else "")
                if not fallback_provider or not self.availability.is_provider_ready(fallback_provider):
                    self.console.emit("EXECUTION", f"Fallback provider {fallback_provider or '-'} is not ready. Skipping.")
                    continue
                selected_fallback_id = fallback_agent_id
                selected_fallback_record = fallback_record
                break

            if selected_fallback_id and selected_fallback_record:
                self.console.emit("FALLBACK", f"task_id={task.task_id} from={agent_id} to={selected_fallback_id} reason=provider_not_ready")
                agent_id = selected_fallback_id
                agent_record = selected_fallback_record
                module_context["agent_id"] = agent_id
                module_context["provider"] = agent_record.provider
                module_context["model"] = agent_record.model_name
            else:
                failed_result = AgentResult(task.task_id, agent_id, TaskStatus.FAILED, {"summary": f"Provider {provider} unavailable and no ready fallback", "files_changed": [], "commands_run": [], "test_results": [], "diff": ""}, 0.0, [f"Provider {provider} unavailable"], [])
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

            if result.status == TaskStatus.FAILED:
                source_provider = self._normalize_provider(agent_record.provider if agent_record else choice.provider)
                if classified:
                    self.provider_budget_router.mark_failure(task, source_provider, classified)

                # Proactive Soft Fallback for all critical/high failures or quota issues
                should_fallback = (
                    classified in {"quota_exhaustion", "auth_fail", "api_timeout", "tcp_timeout"}
                    or (is_gemini and classified in TIMEOUT_ERROR_TYPES)
                    or (task.priority in {Priority.HIGH, Priority.CRITICAL} and result.status == TaskStatus.FAILED)
                )

                if should_fallback:
                    fallback_chain = self.provider_budget_router.preferred_providers(task, choice)
                    # Exclude the failed agent
                    fallback_agent_id = self._select_agent_by_provider_preference(capability, fallback_chain, exclude={agent_id})
                    if fallback_agent_id:
                        self.console.emit("FALLBACK", f"task_id={task.task_id} from={agent_id} to={fallback_agent_id} reason={classified or 'failure'}")
                        fallback_agent = self.local_agents.get(fallback_agent_id)
                        if fallback_agent:
                            result = fallback_agent.run(task, memory_context=memory_context)
                            # Classify again for metrics
                            result_errors = " ".join(result.errors or [])
                            if result_errors:
                                try:
                                    from .external_ai_bridge import ExternalAIBridge
                                    classified = ExternalAIBridge.classify_error(result_errors)
                                except Exception:
                                    pass
            else:
                success_provider = self._normalize_provider(agent_record.provider if agent_record else choice.provider)
                self.provider_budget_router.register_success(task, success_provider)
            quality = self.quality.analyze(task, result)
            if agent_record:
                agent_record.metrics.quality_score = quality.score
                self.metrics.record_result(agent_record, result)
                self.kpi.apply_priority_policy(agent_record)
            self.results[task.task_id] = result
            command_summary = result.output.get("summary", "")
            raw_thoughts = result.output.get("thoughts")
            if raw_thoughts:
                if isinstance(raw_thoughts, list):
                    for item in raw_thoughts:
                        self.session_memory.hybrid.append_agent_thought(session_id=task.session_id or task.task_id, agent_id=agent_id, thought=str(item))
                else:
                    self.session_memory.hybrid.append_agent_thought(session_id=task.session_id or task.task_id, agent_id=agent_id, thought=str(raw_thoughts))
            if result.errors:
                for error in result.errors:
                    self.session_memory.hybrid.append_agent_error(session_id=task.session_id or task.task_id, agent_id=agent_id, error=str(error))
            self.session_memory.hybrid.remember_command(
                session_id=task.session_id or task.task_id,
                agent_id=agent_id,
                command=f"task:{task.type.value}",
                result={"summary": command_summary, "status": result.status.value},
                success=result.status == TaskStatus.DONE,
            )
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
                result.provider = resolved_record.provider
                result.model_name = resolved_record.model_name
                module_context["agent_id"] = result.agent_id
                module_context["provider"] = resolved_record.provider
                module_context["model"] = resolved_record.model_name
            self.module_manager.after_task(task, result, module_context)

            if choice.requires_secondary_review:
                self.console.emit(
                    "SECONDARY_REVIEW",
                    f"task_id={task.task_id} enabled=true reason={choice.reason}",
                )

            self.memory_consolidator.consolidate(session_id=task.session_id or task.task_id, agent_id=agent_id)
            if hasattr(self.message_bus, "publish_session_insights"):
                self.message_bus.publish_session_insights(task.session_id or task.task_id, {"task_id": task.task_id, "agent_id": agent_id, "summary": command_summary, "status": result.status.value})
            self.session_memory.hybrid.clear_session_thoughts(session_id=task.session_id or task.task_id)

            if not quality.passed:
                self.console.emit("REVIEW", f"Качество ниже порога: {', '.join(quality.issues)}")
            ok, fix_task = self.feedback.evaluate(task, result)
            if not ok and fix_task:
                self.console.emit("FIX", "Найдены ошибки, создана задача исправления")
                fix_result = self.run_task(fix_task)
                if fix_result.status == TaskStatus.DONE:
                    return AgentResult(task.task_id, fix_result.agent_id, TaskStatus.DONE, fix_result.output, min(0.8, fix_result.confidence), fix_result.errors, fix_result.next_recommendations, fix_result.provider, fix_result.model_name)
            return result
        finally:
            if agent_record:
                self.lifecycle.mark_idle(agent_record)
                self.autoscaler.scale_down_idle()
            self.log("info", f"[POST-FLIGHT] Task {task.task_id} lifecycle complete")

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
                    return {"status": "failed", "merged": merged, "results": [r.as_dict() for r in final_results], "metrics": self.metrics.snapshot(), "console": self.console.events, "live_trace": self.live_trace_rows, "scheduler": [decision.as_dict() for decision in self.scheduler.decisions], "kernel_modules": self.module_manager.loaded_modules(), "module_state": module_state, "ai_activity": module_state.get("ai_activity", {}), "model_usage": module_state.get("model_usage", {})}
                completed.add(task.task_id)
                pending.pop(task.task_id)
        merged = self.merger.merge(final_results)
        self.console.emit("DONE", "Все критерии выполнены")
        module_state = self.module_manager.finalize()
        return {"status": "done", "merged": merged, "results": [r.as_dict() for r in final_results], "metrics": self.metrics.snapshot(), "console": self.console.events, "live_trace": self.live_trace_rows, "disabled_agents": self.autoscaler.disabled_agents, "enabled_agents": self.autoscaler.enabled_agents, "scheduler": [decision.as_dict() for decision in self.scheduler.decisions], "kernel_modules": self.module_manager.loaded_modules(), "module_state": module_state, "ai_activity": module_state.get("ai_activity", {}), "model_usage": module_state.get("model_usage", {})}

    async def listen_for_tasks(self):
        from .task_listener import TaskListener
        listener = TaskListener(self)
        await listener.start()
