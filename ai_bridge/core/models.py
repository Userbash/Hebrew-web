from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class AgentType(str, Enum):
    CODEX = "codex"
    REVIEWER = "reviewer"
    TESTER = "tester"
    PLANNER = "planner"
    DOCS = "docs"
    EXTERNAL_AI = "external_ai"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    OFFLINE = "offline"
    STARTING = "starting"
    WARMING_UP = "warming_up"
    LOADING_CONTEXT = "loading_context"
    LOADING_TASK_CONTEXT = "loading_task_context"
    READY = "ready"
    IDLE = "idle"
    ASSIGNED = "assigned"
    BUSY = "busy"
    BLOCKED = "blocked"
    WAITING_DEPENDENCY = "waiting_dependency"
    WAITING_INPUT = "waiting_input"
    REVIEWING = "reviewing"
    TESTING = "testing"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    COOLING_DOWN = "cooling_down"
    STANDBY = "standby"
    SLEEPING = "sleeping"
    UNREACHABLE = "unreachable"
    FAILED = "failed"
    RECOVERING = "recovering"
    DRAINING = "draining"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"


class TaskType(str, Enum):
    PLAN = "plan"
    CODE = "code"
    REVIEW = "review"
    TEST = "test"
    DOCS = "docs"
    FIX = "fix"
    RESEARCH = "research"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    WAITING_DEPENDENCY = "waiting_dependency"
    BLOCKED = "blocked"
    RETRYING = "retrying"
    DONE = "done"
    FAILED = "failed"
    CANCELED = "canceled"
    NEEDS_REVIEW = "needs_review"


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(slots=True)
class AgentMetrics:
    agent_id: str = ""
    agent_type: str = "custom"
    model_name: str = "local-small"
    provider: str = "local"
    status: AgentStatus = AgentStatus.READY
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    queue_depth: int = 0
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0
    error_rate: float = 0.0
    token_input: int = 0
    token_output: int = 0
    token_total: int = 0
    estimated_cost: float = 0.0
    token_cost: float = 0.0
    cpu_load: float | None = None
    memory_load: float | None = None
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    idle_since: datetime | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    current_task_id: str | None = None
    current_task_type: str | None = None
    quality_score: float = 1.0
    review_score: float = 1.0
    test_pass_rate: float = 1.0
    priority_score: float = 1.0

    @property
    def idle_time_sec(self) -> float:
        if not self.idle_since:
            return 0.0
        return max(0.0, (datetime.now(UTC) - self.idle_since).total_seconds())

    @property
    def uptime_sec(self) -> float:
        return max(0.0, (datetime.now(UTC) - self.started_at).total_seconds())

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "model_name": self.model_name,
            "provider": self.provider,
            "status": self.status.value,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "queue_depth": self.queue_depth,
            "avg_latency_ms": self.avg_latency_ms,
            "success_rate": self.success_rate,
            "error_rate": self.error_rate,
            "token_input": self.token_input,
            "token_output": self.token_output,
            "token_total": self.token_total,
            "estimated_cost": self.estimated_cost,
            "cpu_load": self.cpu_load,
            "memory_load": self.memory_load,
            "last_seen": self.last_seen.isoformat(),
            "idle_time_sec": self.idle_time_sec,
            "uptime_sec": self.uptime_sec,
            "current_task_id": self.current_task_id,
            "current_task_type": self.current_task_type,
            "quality_score": self.quality_score,
            "review_score": self.review_score,
            "test_pass_rate": self.test_pass_rate,
        }


@dataclass(slots=True)
class AgentKPI:
    delivery_score: float = 1.0
    quality_score: float = 1.0
    stability_score: float = 1.0
    cost_efficiency: float = 1.0
    reuse_score: float = 0.0
    test_success_rate: float = 1.0
    review_pass_rate: float = 1.0

    @property
    def agent_kpi(self) -> float:
        return (
            self.quality_score * 0.30
            + self.test_success_rate * 0.25
            + self.delivery_score * 0.20
            + self.stability_score * 0.15
            + self.cost_efficiency * 0.10
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "delivery_score": self.delivery_score,
            "quality_score": self.quality_score,
            "stability_score": self.stability_score,
            "cost_efficiency": self.cost_efficiency,
            "reuse_score": self.reuse_score,
            "test_success_rate": self.test_success_rate,
            "review_pass_rate": self.review_pass_rate,
            "agent_kpi": self.agent_kpi,
        }


@dataclass(slots=True)
class AgentHealth:
    agent_id: str
    status: AgentStatus
    capabilities: list[str]
    active_tasks: int = 0
    queue_depth: int = 0
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0
    last_error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "active_tasks": self.active_tasks,
            "queue_depth": self.queue_depth,
            "avg_latency_ms": self.avg_latency_ms,
            "success_rate": self.success_rate,
            "last_error": self.last_error,
            "timestamp": self.timestamp,
        }


@dataclass(slots=True)
class AgentRecord:
    id: str
    type: AgentType
    endpoint: str
    capabilities: list[str]
    status: AgentStatus = AgentStatus.READY
    limits: dict[str, Any] = field(default_factory=dict)
    access_key_ref: str | None = None
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    kpi: AgentKPI = field(default_factory=AgentKPI)
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    critical: bool = False
    disabled_reason: str | None = None
    model_name: str = "local-small"
    provider: str = "local"

    def __post_init__(self) -> None:
        self.metrics.agent_id = self.id
        self.metrics.agent_type = self.type.value
        self.metrics.status = self.status
        self.metrics.model_name = self.model_name
        self.metrics.provider = self.provider

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities


@dataclass(slots=True)
class TaskInput:
    description: str
    files: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TaskContext:
    project: str
    repo_path: str
    branch: str


@dataclass(slots=True)
class Task:
    type: TaskType
    input: TaskInput
    context: TaskContext
    priority: Priority = Priority.NORMAL
    task_id: str = field(default_factory=lambda: str(uuid4()))
    parent_task_id: str | None = None
    callback_url: str | None = None
    required_capability: str | None = None
    dependencies: list[str] = field(default_factory=list)
    complexity: Complexity | None = None
    assigned_model: str | None = None
    expected_output: str | None = None
    session_id: str | None = None
    memory_scope: str = "task"
    memory_keys: list[str] = field(default_factory=list)
    memory_ttl_sec: int | None = None
    cache_policy: str = "read_write"
    repo_fingerprint: str | None = None
    retry_count: int = 0
    hop_count: int = 0
    max_hops: int = 5
    review_depth: int = 0


@dataclass(slots=True)
class AtomicTask:
    id: str
    parent_id: str | None
    description: str
    required_capability: str
    complexity: Complexity
    assigned_agent: str | None
    assigned_model: str | None
    dependencies: list[str]
    expected_output: str
    acceptance_criteria: list[str]


@dataclass(slots=True)
class TaskAcceptance:
    task_id: str
    status: TaskStatus
    assigned_agent: str | None
    estimated_complexity: str
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "estimated_complexity": self.estimated_complexity,
            "message": self.message,
        }


@dataclass(slots=True)
class AgentResult:
    task_id: str
    agent_id: str
    status: TaskStatus
    output: dict[str, Any]
    confidence: float
    errors: list[str] = field(default_factory=list)
    next_recommendations: list[str] = field(default_factory=list)
    provider: str | None = None
    model_name: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "provider": self.provider,
            "model": self.model_name,
            "status": self.status.value,
            "output": self.output,
            "confidence": self.confidence,
            "errors": self.errors,
            "next_recommendations": self.next_recommendations,
        }


@dataclass(slots=True)
class QualityReport:
    passed: bool
    score: float
    issues: list[str] = field(default_factory=list)
    requires_review: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "issues": self.issues,
            "requires_review": self.requires_review,
        }


@dataclass(slots=True)
class ScoreBreakdown:
    capability: float
    reliability: float
    latency: float
    cost: float
    context: float
    safety: float

    def total(self, weights: dict[str, float]) -> float:
        return sum(getattr(self, k) * w for k, w in weights.items())

@dataclass(slots=True)
class RoutingTrace:
    rule: str
    category: str
    delta: float
    reason: str


@dataclass(slots=True)
class ExecutionPlan:
    root_task_id: str
    atomic_tasks: list[Task]

    def ready_tasks(self, completed: set[str]) -> list[Task]:
        return [task for task in self.atomic_tasks if all(dep in completed for dep in task.dependencies)]


class ReadinessLevel(str, Enum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"


class P2PMessageType(str, Enum):
    STATUS_UPDATE = "status_update"
    HEARTBEAT = "heartbeat"
    TASK_HANDOFF = "task_handoff"
    REQUEST_CONTEXT = "request_context"
    PROVIDE_CONTEXT = "provide_context"
    TEST_FAILED = "test_failed"
    REVIEW_FAILED = "review_failed"
    FIX_REQUIRED = "fix_required"
    DEPENDENCY_READY = "dependency_ready"
    DEPENDENCY_BLOCKED = "dependency_blocked"
    AGENT_OVERLOADED = "agent_overloaded"
    AGENT_UNAVAILABLE = "agent_unavailable"
    FALLBACK_REQUEST = "fallback_request"
    RESULT_READY = "result_ready"
    RETRY_REQUEST = "retry_request"
    APPROVAL_REQUIRED = "approval_required"


class AckStatus(str, Enum):
    SENT = "sent"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass(slots=True)
class AgentReadiness:
    agent_id: str
    status: AgentStatus
    readiness: ReadinessLevel
    current_tasks: int
    max_tasks: int
    load: float
    capabilities: list[str]
    latency_ms: float
    last_heartbeat: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "readiness": self.readiness.value,
            "current_tasks": self.current_tasks,
            "max_tasks": self.max_tasks,
            "load": self.load,
            "capabilities": self.capabilities,
            "latency_ms": self.latency_ms,
            "last_heartbeat": self.last_heartbeat,
        }


@dataclass(slots=True)
class TaskWeight:
    task_id: str
    priority: int = 5
    risk: int = 1
    complexity: int = 1
    urgency: int = 5
    business_value: int = 5
    dependency_count: int = 0
    estimated_cost: int = 1
    requires_review: bool = False

    @property
    def task_score(self) -> float:
        return (
            self.priority * 0.30
            + self.urgency * 0.20
            + self.business_value * 0.20
            + self.risk * 0.15
            + self.dependency_count * 0.10
            + self.complexity * 0.05
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "priority": self.priority,
            "risk": self.risk,
            "complexity": self.complexity,
            "urgency": self.urgency,
            "business_value": self.business_value,
            "dependency_count": self.dependency_count,
            "estimated_cost": self.estimated_cost,
            "requires_review": self.requires_review,
            "task_score": self.task_score,
        }


@dataclass(slots=True)
class P2PMessage:
    task_id: str
    from_agent: str
    to_agent: str
    message_type: P2PMessageType
    priority: str = "normal"
    requires_orchestrator: bool = False
    payload: dict[str, Any] = field(default_factory=dict)
    route: list[str] = field(default_factory=list)
    delivery_mode: str = "p2p_direct"
    requires_ack: bool = True
    message_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    correlation_id: str | None = None
    idempotency_key: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "task_id": self.task_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type.value,
            "priority": self.priority,
            "requires_orchestrator": self.requires_orchestrator,
            "payload": self.payload,
            "route": self.route,
            "delivery_mode": self.delivery_mode,
            "requires_ack": self.requires_ack,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
        }

@dataclass(slots=True)
class MessageAck:
    message_id: str
    ack_status: AckStatus
    received_by: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "ack_status": self.ack_status.value,
            "received_by": self.received_by,
            "timestamp": self.timestamp,
            "reason": self.reason,
        }


@dataclass(slots=True)
class SchedulerDecision:
    task_id: str
    route_mode: str
    assigned_agent: str | None
    requires_orchestrator: bool
    reason: str
    task_score: float
    agent_score: float = 0.0
    readiness: ReadinessLevel | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "route_mode": self.route_mode,
            "assigned_agent": self.assigned_agent,
            "requires_orchestrator": self.requires_orchestrator,
            "reason": self.reason,
            "task_score": self.task_score,
            "agent_score": self.agent_score,
            "readiness": self.readiness.value if self.readiness else None,
        }

@dataclass(slots=True)
class SecurityPolicy:
    requires_approval: bool = False
    allowed_roles: list[str] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)

@dataclass(slots=True)
class TaskPayload:
    objective: str
    input_data: dict[str, Any]
    context: dict[str, Any]
    acceptance_criteria: list[str]
    expected_output_format: str
    artifacts: list[str] = field(default_factory=list)

@dataclass(slots=True)
class TaskEnvelope:
    protocol_version: str
    task_id: str
    parent_task_id: str | None
    trace_id: str
    correlation_id: str | None
    source_agent: str
    target_agent: str | None
    target_capability: str
    priority: Priority
    qos_class: str
    ttl: int
    deadline: datetime | None = None
    hop_count: int = 0
    max_hops: int = 5
    retry_count: int = 0
    max_retries: int = 3
    security_policy: SecurityPolicy = field(default_factory=SecurityPolicy)
    context_scope: str = "global"
    dependencies: list[str] = field(default_factory=list)
    payload: TaskPayload = field(default_factory=lambda: TaskPayload("init", {}, {}, [], "text"))
    session_id: str | None = None
    idempotency_key: str | None = None
    is_dead_letter: bool = False
    retry_delay_ms: int = 1000
    memory_scope: str = "task"
    memory_keys: list[str] = field(default_factory=list)
    memory_ttl_sec: int | None = None
    cache_policy: str = "read_write"
    repo_fingerprint: str | None = None
    review_depth: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

@dataclass(slots=True)
class ResultPayload:
    task_id: str
    status: TaskStatus
    output: dict[str, Any]
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence: float = 1.0
    completed_criteria: list[str] = field(default_factory=list)
    failed_criteria: list[str] = field(default_factory=list)

@dataclass(slots=True)
class ResultEnvelope:
    protocol_version: str
    result_id: str
    task_id: str
    trace_id: str
    correlation_id: str | None
    source_agent: str
    target_agent: str | None
    status: TaskStatus
    payload: ResultPayload
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

@dataclass(slots=True)
class TaskGraph:
    root_task_id: str
    nodes: dict[str, TaskEnvelope] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=dict)
    status: str = "pending"
    merge_strategy: str = "all_required"

class ProtocolError(Exception):
    pass

def encapsulate(payload: TaskPayload, metadata: dict[str, Any]) -> TaskEnvelope:
    task_id = metadata.get("task_id") or str(uuid4())
    trace_id = metadata.get("trace_id") or str(uuid4())
    return TaskEnvelope(
        protocol_version="1.0",
        task_id=task_id,
        parent_task_id=metadata.get("parent_task_id"),
        trace_id=trace_id,
        correlation_id=metadata.get("correlation_id"),
        source_agent=metadata.get("source_agent", "system"),
        target_agent=metadata.get("target_agent"),
        target_capability=metadata.get("target_capability", "any"),
        priority=metadata.get("priority", Priority.NORMAL),
        qos_class=metadata.get("qos_class", "best_effort"),
        ttl=metadata.get("ttl", 3600),
        deadline=metadata.get("deadline"),
        hop_count=0,
        max_hops=metadata.get("max_hops", 10),
        retry_count=0,
        max_retries=metadata.get("max_retries", 3),
        security_policy=metadata.get("security_policy", SecurityPolicy()),
        context_scope=metadata.get("context_scope", "global"),
        session_id=metadata.get("session_id"),
        memory_scope=metadata.get("memory_scope", "task"),
        memory_keys=metadata.get("memory_keys", []),
        memory_ttl_sec=metadata.get("memory_ttl_sec"),
        cache_policy=metadata.get("cache_policy", "read_write"),
        repo_fingerprint=metadata.get("repo_fingerprint"),
        dependencies=metadata.get("dependencies", []),
        payload=payload
    )

def decapsulate(envelope: TaskEnvelope, agent_capabilities: list[str]) -> TaskPayload:
    if envelope.protocol_version != "1.0":
        raise ProtocolError(f"Unsupported protocol version: {envelope.protocol_version}")
    
    if envelope.deadline and datetime.now(UTC) > envelope.deadline:
        raise ProtocolError(f"Deadline exceeded for task {envelope.task_id}")
    
    if envelope.ttl <= 0:
        raise ProtocolError(f"TTL expired for task {envelope.task_id}")
        
    if envelope.hop_count >= envelope.max_hops:
        raise ProtocolError(f"Max hops ({envelope.max_hops}) exceeded for task {envelope.task_id}")
        
    if envelope.target_capability != "any" and envelope.target_capability not in agent_capabilities:
        raise ProtocolError(f"Agent lacks required capability: {envelope.target_capability}")
        
    return envelope.payload

def task_to_envelope(task: Task) -> TaskEnvelope:
    payload = TaskPayload(
        objective=task.input.description,
        input_data={"constraints": task.input.constraints},
        context={"project": task.context.project, "repo_path": task.context.repo_path, "branch": task.context.branch},
        acceptance_criteria=task.input.acceptance_criteria,
        expected_output_format="text",
        artifacts=task.input.files
    )
    return encapsulate(payload, {
        "task_id": task.task_id,
        "parent_task_id": task.parent_task_id,
        "priority": task.priority,
        "target_capability": task.required_capability or "any",
        "target_agent": task.assigned_model,
        "session_id": task.session_id,
        "memory_scope": task.memory_scope,
        "memory_keys": task.memory_keys,
        "memory_ttl_sec": task.memory_ttl_sec,
        "cache_policy": task.cache_policy,
        "repo_fingerprint": task.repo_fingerprint,
        "dependencies": task.dependencies
    })
