from __future__ import annotations

import os
from dataclasses import dataclass

from .agent_autoscaler import AgentAutoscaler
from .agent_lifecycle import AgentLifecycleManager
from .agent_registry import AgentRegistry
from .feedback_loop import FeedbackLoop
from .healthcheck import HealthChecker
from .host_bridge import HostBridge
from .kpi import KPIEvaluator
from .load_balancer import LoadBalancer
from .memory_consolidator import MemoryConsolidator
from .metrics import MetricsCollector
from .message_bus import MessageBus
from .model_selector import ModelSelector
from .orchestration_config import OrchestrationConfig
from .quality_analyzer import QualityAnalyzer
from .rabbitmq_bus import RabbitMQBus
from .result_merger import ResultMerger
from .security_gate import SecurityGate
from .session_memory import SessionMemory
from .smart_scheduler import SmartScheduler
from .task_decomposer import TaskDecomposer
from .task_router import TaskRouter
from .user_console import UserConsole


@dataclass(slots=True)
class OrchestratorComponents:
    registry: AgentRegistry
    lifecycle: AgentLifecycleManager
    autoscaler: AgentAutoscaler
    load_balancer: LoadBalancer
    model_selector: ModelSelector
    decomposer: TaskDecomposer
    router: TaskRouter
    orchestration_config: OrchestrationConfig
    scheduler: SmartScheduler
    message_bus: MessageBus
    healthcheck: HealthChecker
    feedback: FeedbackLoop
    metrics: MetricsCollector
    kpi: KPIEvaluator
    quality: QualityAnalyzer
    merger: ResultMerger
    console: UserConsole
    security_gate: SecurityGate
    host_bridge: HostBridge
    session_memory: SessionMemory
    memory_consolidator: MemoryConsolidator


class AgentFactory:
    @staticmethod
    def _build_message_bus() -> MessageBus:
        backend = os.getenv("AI_BRIDGE_MESSAGE_BUS_BACKEND", "inmemory").strip().lower()
        if backend == "rabbitmq":
            return RabbitMQBus()
        return MessageBus()

    @staticmethod
    def build(*, registry: AgentRegistry | None = None, retry_limit: int = 3, idle_shutdown_sec: int = 900) -> OrchestratorComponents:
        reg = registry or AgentRegistry()
        lifecycle = AgentLifecycleManager(idle_shutdown_sec=idle_shutdown_sec)
        load_balancer = LoadBalancer()
        model_selector = ModelSelector()
        session_memory = SessionMemory()

        return OrchestratorComponents(
            registry=reg,
            lifecycle=lifecycle,
            autoscaler=AgentAutoscaler(reg, lifecycle),
            load_balancer=load_balancer,
            model_selector=model_selector,
            decomposer=TaskDecomposer(model_selector),
            router=TaskRouter(reg, load_balancer),
            orchestration_config=OrchestrationConfig.from_env(),
            scheduler=SmartScheduler(reg),
            message_bus=AgentFactory._build_message_bus(),
            healthcheck=HealthChecker(reg),
            feedback=FeedbackLoop(retry_limit=retry_limit),
            metrics=MetricsCollector(),
            kpi=KPIEvaluator(),
            quality=QualityAnalyzer(),
            merger=ResultMerger(),
            console=UserConsole(),
            security_gate=SecurityGate(),
            host_bridge=HostBridge(),
            session_memory=session_memory,
            memory_consolidator=MemoryConsolidator(session_memory.hybrid),
        )
