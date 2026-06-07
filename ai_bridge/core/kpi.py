from __future__ import annotations

from .models import AgentKPI, AgentRecord


class KPIEvaluator:
    def __init__(self, threshold: float = 0.65) -> None:
        self.threshold = threshold

    def calculate(self, agent: AgentRecord) -> AgentKPI:
        total = agent.metrics.completed_tasks + agent.metrics.failed_tasks
        stability = 1.0 - agent.metrics.error_rate
        reuse = min(1.0, total / 10) if total else 0.0
        cost_efficiency = max(0.0, min(1.0, 1.0 / (1.0 + agent.metrics.estimated_cost)))
        delivery = max(0.0, min(1.0, 1000.0 / (1000.0 + agent.metrics.avg_latency_ms)))
        aggregate = (delivery + agent.metrics.quality_score + stability + cost_efficiency + reuse + agent.metrics.test_pass_rate + agent.metrics.review_score) / 7.0
        agent.kpi = AgentKPI(
            agent_id=agent.id,
            agent_kpi=aggregate,
            delivery_score=delivery,
            quality_score=agent.metrics.quality_score,
            stability_score=stability,
            cost_efficiency=cost_efficiency,
            reuse_score=reuse,
            test_success_rate=agent.metrics.test_pass_rate,
            review_pass_rate=agent.metrics.review_score,
            efficiency=delivery,
            reliability=stability,
            efficiency_score=aggregate,
            error_rate=agent.metrics.error_rate,
        )
        return agent.kpi

    def below_threshold(self, agent: AgentRecord) -> bool:
        return self.calculate(agent).agent_kpi < self.threshold

    def apply_priority_policy(self, agent: AgentRecord) -> None:
        if self.below_threshold(agent):
            agent.metrics.priority_score = max(0.25, agent.metrics.priority_score * 0.7)
