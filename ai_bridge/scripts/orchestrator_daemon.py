import asyncio
import logging
import sys
import os

try:
    import ai_bridge.core.fix_imports
except ImportError:
    pass

sys.path.insert(0, '/app')

from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.agents.planner_agent import PlannerAgent
from ai_bridge.agents.codex_agent import CodexAgent
from ai_bridge.agents.gemini_cli_agent import GeminiCLIAgent
from ai_bridge.agents.mistral_agent import MistralAgent
from ai_bridge.agents.reviewer_agent import ReviewerAgent
from ai_bridge.agents.tester_agent import TesterAgent
from ai_bridge.agents.frontend_dev_agent import FrontendDevAgent
from ai_bridge.agents.frontend_design_agent import FrontendDesignAgent
from ai_bridge.core.orchestration_config import OrchestrationConfig
from ai_bridge.core.security import SecurityManager, SecurityPolicy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("orchestrator_daemon")


async def main():
    logger.info("Initializing Orchestrator daemon and binding agents...")

    orchestrator = Orchestrator()
    orchestrator.orchestration_config = OrchestrationConfig.from_env()

    security_manager = SecurityManager(SecurityPolicy(allow_shell=True, shell_allowlist=["npx @google/gemini-cli --prompt"]))

    # Prefer mistral for codex-main when MISTRAL key exists (cost-saving mode).
    mistral_key = (os.getenv("MISTRAL_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    openai_auto = os.getenv("AI_BRIDGE_OPENAI_AUTO_MODEL", "true").strip().lower() in {"1", "true", "yes", "on"}
    if openai_auto and openai_key:
        codex_provider = "openai"
        codex_model = os.getenv("CODEX_OPENAI_MODEL", "gpt-5-mini")
    elif mistral_key:
        codex_provider = "mistral"
        codex_model = "mistral-large-latest"
    elif openai_key:
        codex_provider = "openai"
        codex_model = os.getenv("CODEX_OPENAI_MODEL", "gpt-coding-large")
    else:
        codex_provider = "local"
        codex_model = "local-small"

    orchestrator.attach_local_agent("planner-1", PlannerAgent("planner-1"), agent_type="planner", critical=True, model_name="gpt-planner", provider="openai")
    orchestrator.attach_local_agent("codex-main", CodexAgent("codex-main"), agent_type="codex", critical=True, model_name=codex_model, provider=codex_provider)
    orchestrator.attach_local_agent("gemini-cli-1", GeminiCLIAgent("gemini-cli-1", security_manager), agent_type="external_ai", critical=False, model_name="gemini-cli", provider="google")
    orchestrator.attach_local_agent("mistral-1", MistralAgent("mistral-1", security_manager), agent_type="external_ai", critical=False, model_name="mistral-large-latest", provider="mistral")
    orchestrator.attach_local_agent("tester-1", TesterAgent("tester-1"), agent_type="tester", model_name="gpt-test-standard", provider="openai")
    orchestrator.attach_local_agent("reviewer-1", ReviewerAgent("reviewer-1"), agent_type="reviewer", model_name="gpt-review-large", provider="openai")
    orchestrator.attach_local_agent("frontend-dev-1", FrontendDevAgent("frontend-dev-1"), agent_type="codex", model_name=codex_model, provider=codex_provider)
    orchestrator.attach_local_agent("frontend-design-1", FrontendDesignAgent("frontend-design-1"), agent_type="docs", model_name="design-spec", provider="local")

    logger.info(f"System Ready. Agents bound: {len(orchestrator.registry.list_agents())}")
    await orchestrator.listen_for_tasks()


if __name__ == "__main__":
    asyncio.run(main())
