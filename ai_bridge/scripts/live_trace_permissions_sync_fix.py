from __future__ import annotations

from ai_bridge.agents.codex_agent import CodexAgent
from ai_bridge.agents.tester_agent import TesterAgent
from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.orchestrator import Orchestrator


def render_trace_table(rows: list[dict[str, object]]) -> str:
    headers = [
        "task_id",
        "task_type",
        "detected_keywords",
        "matched_high_risk_rules",
        "matched_low_risk_exemptions",
        "final_complexity",
        "selected_provider",
        "selected_model",
        "router_agent",
        "router_provider",
        "fallback",
        "secondary_review",
        "reason",
    ]

    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        vals = [str(row.get(h, "")) for h in headers]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    orchestrator = Orchestrator()

    orchestrator.attach_local_agent(
        "local-orchestrator",
        CodexAgent("local-orchestrator"),
        agent_type="custom",
        critical=False,
        model_name="local-small",
        provider="local",
    )
    orchestrator.attach_local_agent(
        "mistral-orchestrator",
        CodexAgent("mistral-orchestrator"),
        agent_type="custom",
        critical=False,
        model_name="mistral-small-or-medium",
        provider="mistral",
    )
    orchestrator.attach_local_agent(
        "gemini-cli-orchestrator",
        CodexAgent("gemini-cli-orchestrator"),
        agent_type="custom",
        critical=False,
        model_name="gemini-cli",
        provider="google",
    )
    orchestrator.attach_local_agent(
        "openai-orchestrator",
        CodexAgent("openai-orchestrator"),
        agent_type="codex",
        critical=True,
        model_name="gpt-coding-large",
        provider="openai",
    )
    orchestrator.attach_local_agent(
        "openai-secure-orchestrator",
        CodexAgent("openai-secure-orchestrator"),
        agent_type="codex",
        critical=True,
        model_name="gpt-senior-secure",
        provider="openai",
    )
    orchestrator.attach_local_agent(
        "openai-fallback-orchestrator",
        TesterAgent("openai-fallback-orchestrator"),
        agent_type="tester",
        critical=False,
        model_name="gpt-coding-standard",
        provider="openai",
    )

    # Constrain capabilities to match routing policy matrix
    orchestrator.registry.get("local-orchestrator").capabilities = ["docs", "fix"]  # type: ignore[union-attr]
    orchestrator.registry.get("mistral-orchestrator").capabilities = ["code", "fix", "test"]  # type: ignore[union-attr]
    orchestrator.registry.get("gemini-cli-orchestrator").capabilities = ["docs", "research", "review"]  # type: ignore[union-attr]
    orchestrator.registry.get("openai-orchestrator").capabilities = ["plan"]  # type: ignore[union-attr]
    orchestrator.registry.get("openai-secure-orchestrator").capabilities = ["code", "fix", "test", "docs", "research", "review"]  # type: ignore[union-attr]
    orchestrator.registry.get("openai-fallback-orchestrator").capabilities = ["code", "fix", "test"]  # type: ignore[union-attr]

    task = Task(
        TaskType.FIX,
        TaskInput("permissions-sync-fix", acceptance_criteria=["sync complete"]),
        TaskContext("demo", ".", "main"),
    )

    result = orchestrator.run(task)

    print("\n=== LIVE TRACE (table) ===")
    print(render_trace_table(result.get("live_trace", [])))

    print("\n=== PIPELINE EVENTS ===")
    for event in result.get("console", []):
        if event.startswith("[PLAN]") or event.startswith("[SCHEDULER]") or event.startswith("[ROUTING]") or event.startswith("[MODEL_SELECTION]") or event.startswith("[EXECUTION]") or event.startswith("[SECONDARY_REVIEW]") or event.startswith("[DONE]"):
            print(event)


if __name__ == "__main__":
    main()
