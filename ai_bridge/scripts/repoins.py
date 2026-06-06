from __future__ import annotations
import asyncio
import sys
import logging
import os
from pathlib import Path
from datetime import datetime, UTC

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai_bridge.core.orchestrator import Orchestrator
from ai_bridge.core.models import Task, TaskInput, TaskContext, TaskType, Priority, TaskStatus
from ai_bridge.core.agent_factory import AgentFactory
from ai_bridge.core.security import SecurityManager, SecurityPolicy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("repoins")

async def run_repoins():
    """
    Broadcasting 'repoins' (Repository Inspection) to all available agents.
    Each agent provides an inspection report based on its specialized capability.
    """
    print("\n" + "="*80)
    print(f"🚀 BROADCAST REPOSITORY INSPECTION (repoins) - {datetime.now(UTC).isoformat()}")
    print("="*80)

    orchestrator = Orchestrator()
    
    # Ensure local agents are registered
    # Registry already lists them if they were previously attached, 
    # but for a standalone run we ensure they exist.
    security_manager = SecurityManager(SecurityPolicy(allow_shell=True))
    from ai_bridge.agents.planner_agent import PlannerAgent
    from ai_bridge.agents.codex_agent import CodexAgent
    from ai_bridge.agents.reviewer_agent import ReviewerAgent
    from ai_bridge.agents.tester_agent import TesterAgent
    from ai_bridge.agents.gemini_cli_agent import GeminiCLIAgent
    from ai_bridge.agents.mistral_agent import MistralAgent

    agents_to_run = [
        ("planner-1", PlannerAgent("planner-1")),
        ("codex-1", CodexAgent("codex-1")),
        ("reviewer-1", ReviewerAgent("reviewer-1")),
        ("tester-1", TesterAgent("tester-1")),
        ("mistral-1", MistralAgent("mistral-1", security_manager)),
        ("antigravity-cli-1", GeminiCLIAgent("antigravity-cli-1", security_manager))
    ]

    for aid, agent_obj in agents_to_run:
        if not orchestrator.registry.get(aid):
            # Map Agent objects to types for attachment
            atype_map = {
                "planner-1": "planner",
                "codex-1": "codex",
                "reviewer-1": "reviewer",
                "tester-1": "tester",
                "mistral-1": "external_ai",
                "antigravity-cli-1": "external_ai"
            }
            orchestrator.attach_local_agent(aid, agent_obj, agent_type=atype_map[aid])

    agents = orchestrator.registry.list_agents()
    print(f"[*] Identified {len(agents)} active agents for broadcast.")
    
    context = TaskContext(project="hebrew-web", repo_path=".", branch="main")
    reports = []

    for agent_record in agents:
        aid = agent_record.id
        atype = agent_record.type.value
        print(f"\n[▶] Dispatching inspection to: {aid} [{atype}]...")
        
        description = (
            f"Perform a comprehensive repository inspection (repoins). "
            f"Focus on your specific expertise: {atype}. "
            f"Analyze the current state of the codebase, identify potential issues, "
            f"and suggest improvements. Provide a structured markdown report."
        )
        
        task = Task(
            type=TaskType.RESEARCH,
            input=TaskInput(
                description=description,
                acceptance_criteria=["Detailed report provided", "Expertise-specific analysis included"]
            ),
            context=context,
            priority=Priority.NORMAL,
            required_capability=agent_record.capabilities[0] if agent_record.capabilities else "research"
        )
        
        try:
            # Direct execution via agent for broadcast efficiency
            agent = orchestrator.local_agents.get(aid)
            if agent:
                result = agent.run(task)
                
                status_icon = "✅" if result.status == TaskStatus.DONE else "❌"
                print(f"[{status_icon}] Completed with status: {result.status.value}")
                
                summary = result.output.get("summary", "No summary provided.")
                # If the whole output is just a string, it might be in 'summary' or as the output itself
                if isinstance(result.output, str):
                    summary = result.output

                reports.append({
                    "agent_id": aid,
                    "type": atype,
                    "status": result.status.value,
                    "report": summary,
                    "errors": result.errors
                })
            else:
                print(f"[⚠️] No local executor found for {aid}")
        except Exception as e:
            print(f"[🚨] Execution failed: {e}")
            reports.append({
                "agent_id": aid,
                "type": atype,
                "status": "error",
                "report": f"Inspection crashed: {str(e)}",
                "errors": [str(e)]
            })

    # Consolidate results into a final report file
    report_path = Path(".agent/reports/repoins_full_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Repository Inspection (repoins) Full Report\n")
        f.write(f"Date: {datetime.now(UTC).isoformat()}\n\n")
        f.write(f"## Summary Table\n\n")
        f.write("| Agent | Type | Status | Summary |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        
        for r in reports:
            short_summary = r['report'].split('\n')[0][:100] + "..."
            f.write(f"| **{r['agent_id']}** | {r['type']} | {r['status']} | {short_summary} |\n")
        
        f.write("\n---\n\n")
        
        for r in reports:
            f.write(f"## Agent: {r['agent_id']} ({r['type']})\n")
            f.write(f"**Status:** {r['status']}\n\n")
            if r['errors']:
                f.write(f"### Errors\n")
                for err in r['errors']:
                    f.write(f"- {err}\n")
                f.write("\n")
            f.write(f"### Report\n\n{r['report']}\n\n")
            f.write("-" * 40 + "\n\n")

    print("\n" + "="*80)
    print(f"🏁 Broadcast Complete. Full report saved to: {report_path}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(run_repoins())
