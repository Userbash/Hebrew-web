from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class CompatModel(BaseModel):
    model_config = {"validate_assignment": True, "extra": "allow", "use_enum_values": False}

    def as_dict(self) -> dict[str, Any]:
        try:
            return self.model_dump(mode="json")
        except AttributeError:  # pragma: no cover - pydantic v1 fallback
            return self.dict()


class ProtocolError(ValueError):
    pass


class AgentStatus(str, Enum):
    READY = "ready"
    IDLE = "idle"
    BUSY = "busy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    OVERLOADED = "overloaded"
    DISABLED = "disabled"
    FAILED = "failed"
    STARTING = "starting"
    STANDBY = "standby"
    WARMING_UP = "warming_up"
    SLEEPING = "sleeping"
    UNREACHABLE = "unreachable"
    MAINTENANCE = "maintenance"
    DRAINING = "draining"


class AgentType(str, Enum):
    CODEX = "codex"
    TESTER = "tester"
    REVIEWER = "reviewer"
    PLANNER = "planner"
    DOCS = "docs"
    RESEARCH = "research"
    CUSTOM = "custom"


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
    WAITING_INPUT = "waiting_input"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AckStatus(str, Enum):
    SENT = "sent"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    FAILED = "failed"


class P2PMessageType(str, Enum):
    STATUS_UPDATE = "status_update"
    TEST_FAILED = "test_failed"
    CONTEXT_TRANSFER = "context_transfer"
    RESULT = "result"


class ReadinessLevel(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class TaskInput(CompatModel):
    description: str
    files: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)

    def __init__(self, description: str | None = None, **data: Any) -> None:
        if description is not None:
            data.setdefault("description", description)
        super().__init__(**data)


class TaskContext(CompatModel):
    project: str
    repo_path: str | None = None
    branch: str | None = None

    def __init__(self, project: str | None = None, repo_path: str | None = None, branch: str | None = None, **data: Any) -> None:
        if project is not None:
            data.setdefault("project", project)
        if repo_path is not None:
            data.setdefault("repo_path", repo_path)
        if branch is not None:
            data.setdefault("branch", branch)
        super().__init__(**data)


class ResultOutput(CompatModel):
    summary: str = ""
    files_changed: list[str] = Field(default_factory=list)
    commands_run: list[str] = Field(default_factory=list)
    test_results: list[dict[str, Any]] = Field(default_factory=list)
    diff: str | None = None

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class QualityReport(CompatModel):
    passed: bool
    score: float = 0.0
    issues: list[str] = Field(default_factory=list)
    requires_review: bool = False


class RoleProfile(CompatModel):
    name: str
    capabilities: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    escalation_rules: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentMetrics(CompatModel):
    active_tasks: int = 0
    queue_depth: int = 0
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0
    error_rate: float = 0.0
    completed_tasks: int = 0
    failed_tasks: int = 0
    quality_score: float = 1.0
    review_score: float = 1.0
    test_pass_rate: float = 1.0
    estimated_cost: float = 0.0
    token_cost: float = 0.0
    priority_score: float = 1.0
    status: AgentStatus = AgentStatus.READY
    model_name: str | None = None
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    idle_since: datetime | None = None
    current_task_id: str | None = None
    current_task_type: str | None = None

    @property
    def idle_time_sec(self) -> float:
        if self.idle_since is None:
            return 0.0
        return max(0.0, (datetime.now(UTC) - self.idle_since).total_seconds())


class AgentKPI(CompatModel):
    agent_kpi: float = 1.0
    delivery_score: float = 1.0
    quality_score: float = 1.0
    stability_score: float = 1.0
    cost_efficiency: float = 1.0
    reuse_score: float = 1.0
    test_success_rate: float = 1.0
    review_pass_rate: float = 1.0
    error_rate: float = 0.0


class AgentRecord(CompatModel):
    id: str
    type: AgentType = AgentType.CUSTOM
    endpoint: str
    capabilities: list[str]
    limits: dict[str, Any] = Field(default_factory=dict)
    access_key_ref: str | None = None
    critical: bool = False
    model_name: str = "local-small"
    provider: str = "local"
    status: AgentStatus = AgentStatus.READY
    metrics: AgentMetrics = Field(default_factory=AgentMetrics)
    kpi: AgentKPI = Field(default_factory=AgentKPI)
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    disabled_reason: str | None = None

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities


class AgentHealth(CompatModel):
    agent_id: str
    status: AgentStatus
    capabilities: list[str]
    active_tasks: int = 0
    queue_depth: int = 0
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0
    last_error: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Task(CompatModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_task_id: str | None = None
    type: TaskType
    priority: Priority = Priority.NORMAL
    input: TaskInput
    context: TaskContext
    callback_url: str | None = None
    complexity: Complexity | None = None
    required_capability: str | None = None
    retry_count: int = 0
    dependencies: list[str] = Field(default_factory=list)
    draft_layer: str | None = None
    routing_hints: dict[str, Any] = Field(default_factory=dict)
    expected_output: str | None = None
    assigned_model: str | None = None
    session_id: str | None = None
    memory_scope: str = "task"
    cache_policy: str = "read_write"
    memory_keys: list[str] = Field(default_factory=list)
    memory_ttl_sec: int = 3600

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            merged = dict(kwargs)
            for name, value in zip(("type", "input", "context", "priority"), args):
                merged.setdefault(name, value)
            kwargs = merged
        super().__init__(**kwargs)


class AgentResult(CompatModel):
    task_id: str
    agent_id: str
    status: TaskStatus
    output: ResultOutput
    confidence: float = 0.0
    errors: list[str] = Field(default_factory=list)
    next_recommendations: list[str] = Field(default_factory=list)
    provider: str | None = None
    model_name: str | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            fields = ["task_id", "agent_id", "status", "output", "confidence", "errors", "next_recommendations", "provider", "model_name"]
            merged = dict(kwargs)
            for name, value in zip(fields, args):
                merged.setdefault(name, value)
            kwargs = merged
        super().__init__(**kwargs)


class TaskResult(AgentResult):
    pass


class TaskAcceptance(CompatModel):
    task_id: str
    status: TaskStatus
    assigned_agent: str | None = None
    complexity: str = "medium"
    message: str = ""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            fields = ["task_id", "status", "assigned_agent", "complexity", "message"]
            merged = dict(kwargs)
            for name, value in zip(fields, args):
                merged.setdefault(name, value)
            kwargs = merged
        super().__init__(**kwargs)


class SecurityPolicy(CompatModel):
    requires_approval: bool = False
    allow_shell: bool = True


class TaskPayload(CompatModel):
    objective: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    acceptance_criteria: list[str] = Field(default_factory=list)
    expected_output_format: str = "json"
    artifacts: list[str] = Field(default_factory=list)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            fields = ["objective", "input_data", "context", "acceptance_criteria", "expected_output_format", "artifacts"]
            merged = dict(kwargs)
            for name, value in zip(fields, args):
                merged.setdefault(name, value)
            kwargs = merged
        if "files" in kwargs and "artifacts" not in kwargs:
            kwargs["artifacts"] = kwargs.pop("files")
        super().__init__(**kwargs)

    @property
    def files(self) -> list[str]:
        return self.artifacts


class TaskEnvelope(CompatModel):
    protocol_version: str = "1.0"
    task_id: str
    parent_task_id: str | None = None
    trace_id: str
    correlation_id: str | None = None
    source_agent: str = "orchestrator"
    target_agent: str | None = None
    target_capability: str = "any"
    priority: Priority | str = Priority.NORMAL
    qos_class: str = "normal"
    ttl: int = 3600
    deadline: datetime | None = None
    hop_count: int = 0
    max_hops: int = 10
    retry_count: int = 0
    max_retries: int = 3
    security_policy: SecurityPolicy = Field(default_factory=SecurityPolicy)
    context_scope: str = "global"
    dependencies: list[str] = Field(default_factory=list)
    payload: TaskPayload
    is_dead_letter: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            fields = ["protocol_version", "task_id", "parent_task_id", "trace_id", "correlation_id", "source_agent", "target_agent", "target_capability", "priority", "qos_class", "ttl", "deadline", "hop_count", "max_hops", "retry_count", "max_retries", "security_policy", "context_scope", "dependencies", "payload"]
            merged = dict(kwargs)
            for name, value in zip(fields, args):
                if name == "security_policy" and value is None:
                    value = SecurityPolicy()
                merged.setdefault(name, value)
            kwargs = merged
        super().__init__(**kwargs)


class P2PMessage(CompatModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    from_agent: str
    to_agent: str
    message_type: P2PMessageType
    priority: Priority | str = Priority.NORMAL
    payload: dict[str, Any] = Field(default_factory=dict)
    requires_ack: bool = True
    route: list[str] = Field(default_factory=list)
    delivery_mode: str = "direct"
    is_dead_letter: bool = False


class MessageAck(CompatModel):
    message_id: str
    ack_status: AckStatus
    received_by: str
    reason: str | None = None


class ExecutionPlan(CompatModel):
    root_task_id: str
    atomic_tasks: list[Task]
    draft_layers: list[dict[str, Any]] = Field(default_factory=list)


class TaskGraph(CompatModel):
    root_task_id: str | None = None
    nodes: dict[str, TaskEnvelope] = Field(default_factory=dict)
    edges: dict[str, list[str]] = Field(default_factory=dict)


class ResultPayload(CompatModel):
    task_id: str
    status: TaskStatus
    output: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    completed_criteria: list[str] = Field(default_factory=list)
    failed_criteria: list[str] = Field(default_factory=list)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            fields = ["task_id", "status", "output", "artifacts", "errors", "warnings", "confidence", "completed_criteria", "failed_criteria"]
            merged = dict(kwargs)
            for name, value in zip(fields, args):
                merged.setdefault(name, value)
            kwargs = merged
        super().__init__(**kwargs)


class ResultEnvelope(CompatModel):
    protocol_version: str = "1.0"
    result_id: str
    task_id: str
    trace_id: str
    correlation_id: str | None = None
    source_agent: str
    target_agent: str | None = None
    status: TaskStatus
    payload: ResultPayload

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            fields = ["protocol_version", "result_id", "task_id", "trace_id", "correlation_id", "source_agent", "target_agent", "status", "payload"]
            merged = dict(kwargs)
            for name, value in zip(fields, args):
                merged.setdefault(name, value)
            kwargs = merged
        super().__init__(**kwargs)


class TaskWeight(CompatModel):
    task_id: str
    priority: int
    risk: int
    complexity: int
    urgency: int
    business_value: int
    dependency_count: int
    estimated_cost: int
    requires_review: bool

    @property
    def task_score(self) -> float:
        return float(self.priority + self.risk + self.complexity + self.urgency + self.business_value + self.dependency_count + self.estimated_cost)


class AgentReadiness(CompatModel):
    agent_id: str
    status: AgentStatus
    readiness: ReadinessLevel
    current_tasks: int
    max_tasks: int
    load: float
    capabilities: list[str]
    latency_ms: float
    last_heartbeat: str


class SchedulerDecision(CompatModel):
    task_id: str
    route_mode: str
    assigned_agent: str | None
    requires_orchestrator: bool
    reason: str
    task_score: float
    agent_score: float | None = None
    readiness: ReadinessLevel | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            fields = ["task_id", "route_mode", "assigned_agent", "requires_orchestrator", "reason", "task_score", "agent_score", "readiness"]
            merged = dict(kwargs)
            for name, value in zip(fields, args):
                merged.setdefault(name, value)
            kwargs = merged
        super().__init__(**kwargs)


def encapsulate(payload: TaskPayload | Task, metadata: dict[str, Any] | None = None) -> TaskEnvelope:
    metadata = metadata or {}
    if isinstance(payload, Task):
        task_payload = TaskPayload(
            objective=payload.input.description,
            input_data={},
            context=payload.context.as_dict(),
            acceptance_criteria=list(payload.input.acceptance_criteria),
            expected_output_format="json",
            artifacts=list(payload.input.files),
        )
        task_id = payload.task_id
        parent_task_id = payload.parent_task_id
        priority = payload.priority
        target_capability = payload.required_capability or payload.type.value
        retry_count = payload.retry_count
        dependencies = list(payload.dependencies)
    else:
        task_payload = payload
        task_id = metadata.get("task_id") or str(uuid4())
        parent_task_id = metadata.get("parent_task_id")
        priority = metadata.get("priority", Priority.NORMAL)
        target_capability = metadata.get("target_capability", "any")
        retry_count = int(metadata.get("retry_count", 0))
        dependencies = list(metadata.get("dependencies", []))

    return TaskEnvelope(
        protocol_version=str(metadata.get("protocol_version", "1.0")),
        task_id=task_id,
        parent_task_id=parent_task_id,
        trace_id=str(metadata.get("trace_id") or uuid4()),
        correlation_id=metadata.get("correlation_id"),
        source_agent=metadata.get("source_agent", "orchestrator"),
        target_agent=metadata.get("target_agent"),
        target_capability=target_capability,
        priority=priority,
        qos_class=metadata.get("qos_class", "normal"),
        ttl=int(metadata.get("ttl", 3600)),
        deadline=metadata.get("deadline"),
        hop_count=int(metadata.get("hop_count", 0)),
        max_hops=int(metadata.get("max_hops", 10)),
        retry_count=retry_count,
        max_retries=int(metadata.get("max_retries", 3)),
        security_policy=metadata.get("security_policy") or SecurityPolicy(),
        context_scope=metadata.get("context_scope", "global"),
        dependencies=dependencies,
        payload=task_payload,
    )


def decapsulate(envelope: TaskEnvelope, agent_capabilities: list[str]) -> TaskPayload:
    if envelope.protocol_version != "1.0":
        raise ProtocolError(f"Unsupported protocol version: {envelope.protocol_version}")
    if envelope.deadline and datetime.now(UTC) > envelope.deadline:
        raise ProtocolError("Deadline exceeded")
    if envelope.ttl <= 0:
        raise ProtocolError("TTL expired")
    if envelope.hop_count >= envelope.max_hops:
        raise ProtocolError(f"Max hops ({envelope.max_hops}) exceeded")
    required = envelope.target_capability
    if required not in {"any", "*"} and required not in agent_capabilities:
        raise ProtocolError(f"Agent lacks required capability: {required}")
    return envelope.payload
