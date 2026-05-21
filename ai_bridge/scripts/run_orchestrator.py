from __future__ import annotations

import argparse

from ai_bridge.agents.codex_agent import CodexAgent
from ai_bridge.agents.gemini_agent import GeminiAgent
from ai_bridge.agents.gemini_cli_agent import GeminiCLIAgent
from ai_bridge.agents.planner_agent import PlannerAgent
from ai_bridge.agents.reviewer_agent import ReviewerAgent
from ai_bridge.agents.tester_agent import TesterAgent
from ai_bridge.core.models import Task, TaskContext, TaskInput, TaskType
from ai_bridge.core.orchestration_config import OrchestrationConfig
from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.core.security import SecurityManager, SecurityPolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AI Bridge orchestration demo")
    parser.add_argument("--yes", action="store_true", help="Auto-approve safe standard tasks")
    parser.add_argument("--auto", action="store_true", help="Enable automatic route/retry/review/test behavior")
    parser.add_argument("--use-bridge", action="store_true", help="Use AI Bridge as the default orchestration engine")
    parser.add_argument("--non-interactive", action="store_true", help="Disable y/n prompts for safe standard tasks")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = OrchestrationConfig.from_env()
    config.apply_cli_flags(yes=args.yes, auto=args.auto, use_bridge=args.use_bridge, non_interactive=args.non_interactive)

    orchestrator = Orchestrator()
    orchestrator.orchestration_config = config
    
    security_manager = SecurityManager(SecurityPolicy(allow_shell=True, shell_allowlist=["npx @google/gemini-cli generate"]))
    
    orchestrator.attach_local_agent("planner-1", PlannerAgent("planner-1"), agent_type="planner", critical=True, model_name="gpt-planner", provider="openai")
    orchestrator.attach_local_agent("codex-main", CodexAgent("codex-main"), agent_type="codex", critical=True, model_name="gpt-coding-large", provider="openai")
    orchestrator.attach_local_agent("gemini-cli-1", GeminiCLIAgent("gemini-cli-1", security_manager), agent_type="external_ai", critical=False, model_name="gemini-cli", provider="google")
    orchestrator.attach_local_agent("tester-1", TesterAgent("tester-1"), agent_type="tester", model_name="gpt-test-standard", provider="openai")
    orchestrator.attach_local_agent("reviewer-1", ReviewerAgent("reviewer-1"), agent_type="reviewer", model_name="gpt-review-large", provider="openai")
    
    task = Task(TaskType.PLAN, TaskInput("Create a small feature", acceptance_criteria=["tests pass"]), TaskContext("demo", ".", "main"))
    print(orchestrator.run(task))


if __name__ == "__main__":
    main()
