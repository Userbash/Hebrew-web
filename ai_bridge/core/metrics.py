from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .models import AgentMetrics, AgentRecord, AgentResult, TaskStatus


@dataclass(slots=True)
class MetricsCollector:
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    latencies: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    agent_metrics: dict[str, AgentMetrics] = field(default_factory=dict)

    def increment(self, name: str, amount: int = 1) -> None:
        self.counters[name] += amount

    def observe_latency(self, agent_id: str, latency_ms: float) -> None:
        self.latencies[agent_id].append(latency_ms)
        if agent_id in self.agent_metrics:
            self.agent_metrics[agent_id].avg_latency_ms = self.average_latency(agent_id)

    def register_agent(self, agent: AgentRecord) -> None:
        self.agent_metrics[agent.id] = agent.metrics

    def record_result(self, agent: AgentRecord, result: AgentResult, latency_ms: float = 0.0) -> None:
        self.register_agent(agent)
        if latency_ms:
            self.observe_latency(agent.id, latency_ms)
        if result.status == TaskStatus.DONE:
            agent.metrics.completed_tasks += 1
        else:
            agent.metrics.failed_tasks += 1
        total = agent.metrics.completed_tasks + agent.metrics.failed_tasks
        agent.metrics.success_rate = agent.metrics.completed_tasks / total if total else 1.0
        agent.metrics.error_rate = agent.metrics.failed_tasks / total if total else 0.0
        agent.metrics.quality_score = min(agent.metrics.quality_score, result.confidence)
        agent.metrics.status = agent.status
        self.increment(f"task.{result.status.value}")

    def average_latency(self, agent_id: str) -> float:
        values = self.latencies.get(agent_id, [])
        return sum(values) / len(values) if values else 0.0

    def snapshot(self) -> dict:
        return {
            "counters": dict(self.counters),
            "avg_latency_ms": {agent_id: self.average_latency(agent_id) for agent_id in self.latencies},
            "agents": {
                agent_id: (metrics.as_dict() if hasattr(metrics, "as_dict") else vars(metrics))
                for agent_id, metrics in self.agent_metrics.items()
            },
        }
