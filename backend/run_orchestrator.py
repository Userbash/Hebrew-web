import asyncio
import logging

from ai_bridge.core.dependency_manager import DependencyManager
from ai_bridge.core.orchestrator import Orchestrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("orchestrator_daemon")


async def main():
    logger.info("Initializing Orchestrator daemon...")
    DependencyManager.ensure_required()
    missing_optional = DependencyManager.find_missing()["optional"]
    if missing_optional:
        logger.info("Optional AI libs are missing: %s", ", ".join(missing_optional))

    orchestrator = Orchestrator()
    logger.info("Starting background TaskListener...")
    await orchestrator.listen_for_tasks()


if __name__ == "__main__":
    asyncio.run(main())
