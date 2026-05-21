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
    READY = "ready"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    IDLE = "idle"
    DEGRADED = "degraded"
    DISABLED = "disabled"
    FAILED = "failed"


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
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
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

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
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
class ExecutionPlan:
    root_task_id: str
    atomic_tasks: list[Task]

    def ready_tasks(self, completed: set[str]) -> list[Task]:
        return [task for task in self.atomic_tasks if all(dep in completed for dep in task.dependencies)]
