import asyncio
import logging
import sys
import os

# Fix for mistralai import issue in instructor library
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
from ai_bridge.core.orchestration_config import OrchestrationConfig
from ai_bridge.core.security import SecurityManager, SecurityPolicy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("orchestrator_daemon")

async def main():
    logger.info("Initializing Orchestrator daemon and binding agents...")
    
    orchestrator = Orchestrator()
    orchestrator.orchestration_config = OrchestrationConfig.from_env()
    
    security_manager = SecurityManager(SecurityPolicy(allow_shell=True, shell_allowlist=["npx @google/gemini-cli --prompt"]))
    
    # Регистрация агентов и привязка к ядру
    orchestrator.attach_local_agent("planner-1", PlannerAgent("planner-1"), agent_type="planner", critical=True, model_name="gpt-planner", provider="openai")
    orchestrator.attach_local_agent("codex-main", CodexAgent("codex-main"), agent_type="codex", critical=True, model_name="gpt-coding-large", provider="openai")
    orchestrator.attach_local_agent("gemini-cli-1", GeminiCLIAgent("gemini-cli-1", security_manager), agent_type="external_ai", critical=False, model_name="gemini-cli", provider="google")
    orchestrator.attach_local_agent("mistral-1", MistralAgent("mistral-1", security_manager), agent_type="external_ai", critical=False, model_name="mistral-large-latest", provider="mistral")
    orchestrator.attach_local_agent("tester-1", TesterAgent("tester-1"), agent_type="tester", model_name="gpt-test-standard", provider="openai")
    orchestrator.attach_local_agent("reviewer-1", ReviewerAgent("reviewer-1"), agent_type="reviewer", model_name="gpt-review-large", provider="openai")
    
    logger.info(f"System Ready. Agents bound: {len(orchestrator.registry.list_agents())}")
    
    # Фоновый режим прослушивания задач
    await orchestrator.listen_for_tasks()

if __name__ == "__main__":
    asyncio.run(main())
