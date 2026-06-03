from __future__ import annotations
import asyncio
import hashlib
import json
import os
import time
from typing import Any
from datetime import UTC, datetime

from ai_bridge.agents.base_agent import BaseAgent

from .agent_factory import AgentFactory
from .agent_registry import AgentRegistry
from .feedback_loop import FeedbackLoop
from .healthcheck import HealthChecker
from .host_bridge import HostBridge
from .kpi import KPIEvaluator
from .load_balancer import LoadBalancer, is_agent_routable
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
from .availability import ModelAvailability, ModelAvailabilityModule, ProviderStatus
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
from .kpi_event_logger import KPIEventLogger
from .ui_design_system_module import UIDesignSystemModule
from .ui_anti_template_module import UIAntiTemplateModule
from .frontend_engineering_bridge_module import FrontendEngineeringBridgeModule
from .autodev_pipeline_module import AutodevPipelineModule
from .testing_module import TestingModule
from .vision_design_audit_module import VisionDesignAuditModule
from .design_learning_module import DesignLearningModule
from .local_llm_bridge import LocalLLMBridge
from .local_llm_module import LocalLLMModule


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

    @staticmethod
    def _local_llm_autostart_enabled() -> bool:
        return os.getenv("AI_BRIDGE_AUTOSTART_LOCAL_LLM", "false").strip().lower() in {"1", "true", "yes", "on"}

    def _autostart_local_llm(self) -> None:
        if os.getenv("TESTING") == "true" or not self._local_llm_autostart_enabled():
            return

        module = self.module_manager.get_module("local_llm")
        if not isinstance(module, LocalLLMModule):
            self.log("warning", "[LOCAL_LLM] local_llm module is not registered; skipping autostart.")
            return

        try:
            ready = self.local_llm_bridge.ensure_ready(module.model_name)
        except Exception as exc:
            self.log("warning", f"[LOCAL_LLM] Autostart failed: {exc}")
            return

        if ready:
            self.log("info", f"[LOCAL_LLM] Autostart complete for {module.model_name}.")
            if os.getenv("AI_BRIDGE_AUTORUN_TEST_SUITE", "true").strip().lower() in {"1", "true", "yes", "on"}:
                try:
                    suite = self.run_test_suite(project_root=os.getenv("AI_BRIDGE_PROJECT_ROOT", "."))
                except RuntimeError as exc:
                    self.log("warning", f"[TESTING] Autostart suite skipped: {exc}")
                else:
                    self.log("info", f"[TESTING] Autostart suite completed ok={suite.get('ok')}")
        else:
            self.log("warning", f"[LOCAL_LLM] Autostart could not confirm readiness for {module.model_name}.")

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
        self.kpi_events = KPIEventLogger.from_env()
        self.local_llm_bridge = LocalLLMBridge(host_bridge=self.host_bridge)
        
        self.module_manager = KernelModuleManager()
        self.module_manager.set_api(self)
        self.module_manager.register(AIActivityModule())
        self.module_manager.register(OrchestratorControlModule())
        self.module_manager.register(ModelUsageModule())
        self.module_manager.register(ModelAvailabilityModule())
        self.module_manager.register(APIBridgeModule())
        self.module_manager.register(SmartDecomposerModule())
        self.module_manager.register(PromptOptimizerModule())
        self.module_manager.register(ChatBusModule())
        self.module_manager.register(TriggerDispatcherModule())
        self.module_manager.register(JSONThemesModule())
        self.module_manager.register(UnifiedVFSModule())
        self.module_manager.register(ColdBootModule())
        self.module_manager.register(UIDesignSystemModule())
        self.module_manager.register(UIAntiTemplateModule())
        self.module_manager.register(FrontendEngineeringBridgeModule())
        self.module_manager.register(AutodevPipelineModule())
        self.module_manager.register(TestingModule())
        self.module_manager.register(VisionDesignAuditModule())
        self.module_manager.register(DesignLearningModule())
        self.module_manager.register(LocalLLMModule())
        
        self.module_manager.load("ai_activity")
        self.module_manager.load("orchestrator_control")
        self.module_manager.load("model_usage")
        self.module_manager.load("model_availability")
        self.module_manager.load("api_bridge")
        self.module_manager.load("smart_decomposer")
        self.module_manager.load("prompt_optimizer")
        self.module_manager.load("chat_bus")
        self.module_manager.load("trigger_dispatcher")
        self.module_manager.load("json_themes")
        self.module_manager.load("unified_vfs")
        self.module_manager.load("cold_boot")
        self.module_manager.load("ui_design_system")
        self.module_manager.load("ui_anti_template")
        self.module_manager.load("frontend_engineering_bridge")
        self.module_manager.load("autodev_pipeline")
        self.module_manager.load("testing")
        self.module_manager.load("vision_design_audit")
        self.module_manager.load("design_learning")
        self._autostart_local_llm()
        
        # Load local_llm only if not in testing environment
        if os.getenv("TESTING") != "true":
            self.module_manager.load("local_llm")

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
        self.kpi_events = KPIEventLogger.from_env()

        self.module_manager = KernelModuleManager()
        self.module_manager.set_api(self)
        self.module_manager.register(AIActivityModule())
        self.module_manager.register(OrchestratorControlModule())
        self.module_manager.register(ModelUsageModule())
        self.module_manager.register(ModelAvailabilityModule())
        self.module_manager.register(APIBridgeModule())
        self.module_manager.register(SmartDecomposerModule())
        self.module_manager.register(PromptOptimizerModule())
        self.module_manager.register(ChatBusModule())
        self.module_manager.register(TriggerDispatcherModule())
        self.module_manager.register(ColdBootModule())
        self.module_manager.load("ai_activity")
        self.module_manager.load("orchestrator_control")
        self.module_manager.load("model_usage")
        self.module_manager.load("model_availability")
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
        session_id = str(normalized.get("session_id") or "default")
        idem_raw = json.dumps(normalized, sort_keys=True, ensure_ascii=True)
        idempotency_key = hashlib.sha256(idem_raw.encode("utf-8")).hexdigest()
        cache_key = f"submit:{idempotency_key}"
        cached = self.session_memory.get(MemoryScope.SESSION, session_id, cache_key)
        if isinstance(cached, dict) and cached.get("status") in {"done", "failed"}:
            self.console.emit("IDEMPOTENCY", f"cache hit for session={session_id} key={idempotency_key[:12]}")
            return cached

        # Try to use trigger dispatcher for semantic routing if message is provided
        message = normalized.get("message") or normalized.get("description")
        if isinstance(message, str) and message:
            trigger_mod = self.module_manager.get_module("trigger_dispatcher")
            if isinstance(trigger_mod, TriggerDispatcherModule):
                triggered = trigger_mod.process_chat_input(message)
                if triggered:
                    # Merge triggered data into normalized payload
                    normalized.update(triggered)

        task = create_standard_task(normalized)
        control = self._control_module()
        if control is not None:
            control.register_submission(task, source=source)
        result = self.run(task)
        self.session_memory.set(MemoryScope.SESSION, session_id, cache_key, result, ttl_sec=3600)
        return result

    def run_autodev_pipeline(self, specs: str, project_root: str = ".", figma_api_available: bool = False) -> dict[str, object]:
        module = self.module_manager.get_module("autodev_pipeline")
        if not isinstance(module, AutodevPipelineModule):
            raise RuntimeError("autodev_pipeline module is not loaded")
        return module.run_pipeline(specs=specs, project_root=project_root, figma_api_available=figma_api_available)

    def run_test_suite(self, project_root: str = ".") -> dict[str, object]:
        module = self.module_manager.get_module("testing")
        if not isinstance(module, TestingModule):
            raise RuntimeError("testing module is not loaded")
        return module.run_suite(project_root=project_root)

    def run_design_audit(self, url: str | None = None, output_dir: str = "test-results") -> dict[str, object]:
        module = self.module_manager.get_module("vision_design_audit")
        if not isinstance(module, VisionDesignAuditModule):
            raise RuntimeError("vision_design_audit module is not loaded")
        result = module.run_audit(url=url, output_dir=output_dir)
        learning = self.learn_design_from_audit(result)
        result["learning"] = learning
        return result

    def learn_design_from_audit(self, audit_report: dict[str, object], session_id: str = "design-learning") -> dict[str, object]:
        module = self.module_manager.get_module("design_learning")
        if not isinstance(module, DesignLearningModule):
            raise RuntimeError("design_learning module is not loaded")
        return module.learn_from_audit(audit_report, session_id=session_id)

    def design_learning_status(self) -> dict[str, object]:
        module = self.module_manager.get_module("design_learning")
        if isinstance(module, DesignLearningModule):
            return module.finalize()
        return {"status": "inactive", "episodes": 0, "patterns": {}, "last_plan": {}}

    def local_llm_status(self) -> dict[str, object]:
        module = self.module_manager.get_module("local_llm")
        if isinstance(module, LocalLLMModule):
            return {"module": module.finalize(), "profile": module.task_profile()}
        return {"module": None, "profile": None}

    def testing_status(self) -> dict[str, object]:
        module = self.module_manager.get_module("testing")
        if isinstance(module, TestingModule):
            return {"module": module.status(), "final": module.finalize()}
        return {"module": None, "final": None}

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

    def _select_agent_by_provider_preference(self, capability: str, providers: list[str], exclude: set[str] | None = None, priority: Priority | str | None = None) -> str | None:
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
                if not is_agent_routable(record, priority):
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

    def _find_fallback_agent(self, capability: str, providers: list[str], exclude: set[str], priority: Priority | str | None = None) -> str | None:
        for provider in providers:
            for record in self.registry.list_agents():
                if record.id in exclude:
                    continue
                if record.provider != provider:
                    continue
                if capability not in record.capabilities:
                    continue
                if not is_agent_routable(record, priority):
                    continue
                if record.id in self.local_agents:
                    return record.id
        return None

    def run_task(self, task: Task) -> AgentResult:
        started_at = datetime.now(UTC)
        started_perf = time.perf_counter()
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
        preferred_agent_id = self._select_agent_by_provider_preference(capability, preferred_providers, priority=task.priority)
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
        fallback_count = 1 if fallback else 0

        module_context["agent_id"] = agent_id
        module_context["provider"] = agent_record.provider if agent_record else choice.provider
        module_context["model"] = agent_record.model_name if agent_record else choice.model_name
        module_context["fallback"] = fallback

        self.console.emit(
            "ROUTING",
            f"task_id={task.task_id} router_agent={agent_id} router_provider={agent_record.provider if agent_record else '-'} "
            f"fallback={fallback} secondary_review={choice.requires_secondary_review}",
        )

        # Pre-flight provider diagnostics: verify DNS/TCP/API/model readiness before spending a task attempt.
        provider = self._normalize_provider(agent_record.provider if agent_record else choice.provider)
        preflight_live = os.getenv("AI_BRIDGE_PREFLIGHT_LIVE_PROBE", "false").strip().lower() in {"1", "true", "yes", "on"}
        provider_health = self.availability.check_provider(provider, live=preflight_live)
        module_context["availability_preflight"] = provider_health.as_dict()
        provider_ready = provider_health.status in {ProviderStatus.HEALTHY, ProviderStatus.DEGRADED}
        if not provider_ready:
            diag = provider_health.as_dict()
            self.console.emit(
                "EXECUTION",
                f"Provider {provider} is not ready ({provider_health.status.value}: {provider_health.error or 'no details'}). Trying fallback providers.",
            )
            fallback_chain = self.provider_budget_router.preferred_providers(task, choice)
            selected_fallback_id = None
            selected_fallback_record = None
            selected_fallback_health = None

            for candidate_provider in fallback_chain:
                fallback_agent_id = self._select_agent_by_provider_preference(capability, [candidate_provider], exclude={agent_id}, priority=task.priority)
                if not fallback_agent_id:
                    continue
                fallback_record = self.registry.get(fallback_agent_id)
                fallback_provider = self._normalize_provider(fallback_record.provider if fallback_record else "")
                if not fallback_provider:
                    continue
                fallback_health = self.availability.check_provider(fallback_provider, live=preflight_live)
                fallback_ready = fallback_health.status in {ProviderStatus.HEALTHY, ProviderStatus.DEGRADED}
                if not fallback_ready:
                    self.console.emit(
                        "EXECUTION",
                        f"Fallback provider {fallback_provider} is not ready ({fallback_health.status.value}: {fallback_health.error or 'no details'}). Skipping.",
                    )
                    continue
                selected_fallback_id = fallback_agent_id
                selected_fallback_record = fallback_record
                selected_fallback_health = fallback_health
                break

            if selected_fallback_id and selected_fallback_record:
                self.console.emit("FALLBACK", f"task_id={task.task_id} from={agent_id} to={selected_fallback_id} reason=preflight_{provider_health.status.value}")
                fallback_count += 1
                agent_id = selected_fallback_id
                agent_record = selected_fallback_record
                module_context["agent_id"] = agent_id
                module_context["provider"] = agent_record.provider
                module_context["model"] = agent_record.model_name
                if selected_fallback_health is not None:
                    module_context["fallback_availability_preflight"] = selected_fallback_health.as_dict()
            else:
                summary = f"Provider {provider} unavailable and no ready fallback"
                failed_result = AgentResult(task.task_id, agent_id, TaskStatus.FAILED, {"summary": summary, "files_changed": [], "commands_run": [], "test_results": [], "diff": "", "provider_diagnostics": diag}, 0.0, [f"Provider {provider} unavailable: {provider_health.status.value}: {provider_health.error or 'no details'}"], [])
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
                    self.availability.record_failure(source_provider, classified, result_errors)

                # Proactive Soft Fallback for all critical/high failures or quota issues
                should_fallback = (
                    classified in {"quota_exhaustion", "auth_fail", "api_timeout", "tcp_timeout"}
                    or (is_gemini and classified in TIMEOUT_ERROR_TYPES)
                    or (task.priority in {Priority.HIGH, Priority.CRITICAL} and result.status == TaskStatus.FAILED)
                )

                if should_fallback:
                    fallback_chain = self.provider_budget_router.preferred_providers(task, choice)
                    # Exclude the failed agent
                    fallback_agent_id = self._select_agent_by_provider_preference(capability, fallback_chain, exclude={agent_id}, priority=task.priority)
                    if fallback_agent_id:
                        self.console.emit("FALLBACK", f"task_id={task.task_id} from={agent_id} to={fallback_agent_id} reason={classified or 'failure'}")
                        fallback_count += 1
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
            finished_at = datetime.now(UTC)
            latency_ms = round((time.perf_counter() - started_perf) * 1000.0, 2)
            model_usage_state = self.module_manager.finalize().get("model_usage", {})
            history = model_usage_state.get("history", []) if isinstance(model_usage_state, dict) else []
            tokens_used = None
            if isinstance(history, list) and history:
                for item in reversed(history):
                    if isinstance(item, dict) and item.get("task_id") == task.task_id:
                        tokens_used = item.get("tokens_used")
                        break
            self.kpi_events.write({
                "event_type": "task_lifecycle",
                "task_id": task.task_id,
                "task_type": task.type.value,
                "priority": task.priority.value,
                "status": result.status.value,
                "agent_id": result.agent_id,
                "provider": result.provider or module_context.get("provider"),
                "model": result.model_name or module_context.get("model"),
                "fallback_count": fallback_count,
                "fallback_used": fallback_count > 0,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "latency_ms": latency_ms,
                "tokens_used": tokens_used,
                "errors_count": len(result.errors or []),
            })

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
                    return {"status": "failed", "merged": merged, "results": [r.as_dict() for r in final_results], "metrics": self.metrics.snapshot(), "console": self.console.events, "live_trace": self.live_trace_rows, "scheduler": [decision.as_dict() for decision in self.scheduler.decisions], "kernel_modules": self.module_manager.loaded_modules(), "module_state": module_state, "ai_activity": module_state.get("ai_activity", {}), "model_usage": module_state.get("model_usage", {}), "model_availability": module_state.get("model_availability", {})}
                completed.add(task.task_id)
                pending.pop(task.task_id)
        merged = self.merger.merge(final_results)
        self.console.emit("DONE", "Все критерии выполнены")
        module_state = self.module_manager.finalize()
        return {"status": "done", "merged": merged, "results": [r.as_dict() for r in final_results], "metrics": self.metrics.snapshot(), "console": self.console.events, "live_trace": self.live_trace_rows, "disabled_agents": self.autoscaler.disabled_agents, "enabled_agents": self.autoscaler.enabled_agents, "scheduler": [decision.as_dict() for decision in self.scheduler.decisions], "kernel_modules": self.module_manager.loaded_modules(), "module_state": module_state, "ai_activity": module_state.get("ai_activity", {}), "model_usage": module_state.get("model_usage", {}), "model_availability": module_state.get("model_availability", {})}

    async def listen_for_tasks(self):
        from .task_listener import TaskListener
        listener = TaskListener(self)
        await listener.start()
