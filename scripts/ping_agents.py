import json
import logging
from ai_bridge.agents.planner_agent import PlannerAgent
from ai_bridge.agents.codex_agent import CodexAgent
from ai_bridge.agents.antigravity_cli_agent import AntigravityCLIAgent
from ai_bridge.agents.mistral_agent import MistralAgent
from ai_bridge.agents.reviewer_agent import ReviewerAgent
from ai_bridge.agents.tester_agent import TesterAgent
from ai_bridge.core.models import Task, TaskType, Priority, TaskInput, TaskContext
from ai_bridge.core.security import SecurityManager, SecurityPolicy

logging.basicConfig(level=logging.ERROR)

def main():
    security_manager = SecurityManager(SecurityPolicy(allow_shell=True, shell_allowlist=["agy -p", "antigravity -p"]))
    
    agents = [
        PlannerAgent("planner-1"),
        CodexAgent("codex-main"),
        AntigravityCLIAgent("antigravity-cli-1", security_manager),
        MistralAgent("mistral-1", security_manager),
        TesterAgent("tester-1"),
        ReviewerAgent("reviewer-1")
    ]
    
    responses = {}
    
    for agent in agents:
        task_id = f"ping-{agent.agent_id}"
        t_type = TaskType.RESEARCH
        if isinstance(agent, PlannerAgent): t_type = TaskType.PLAN
        if isinstance(agent, CodexAgent): t_type = TaskType.CODE
        if isinstance(agent, ReviewerAgent): t_type = TaskType.REVIEW
        if isinstance(agent, TesterAgent): t_type = TaskType.TEST
        
        task_input = TaskInput(description="System ping. Reply with your status and capabilities.")
        task_context = TaskContext(project="hebrew-web", repo_path=".", branch="main")
        
        task = Task(
            task_id=task_id, 
            type=t_type, 
            priority=Priority.NORMAL, 
            input=task_input, 
            context=task_context
        )
        
        try:
            # For Mistral or external APIs, execute() might need async if not properly wrapper in base agent
            # Wait, base_agent.py had def execute(self, task) -> AgentResult
            result = agent.execute(task)
            
            responses[agent.agent_id] = {
                "status": result.status.value,
                "output": result.output,
                "confidence": result.confidence
            }
        except Exception as e:
            responses[agent.agent_id] = {"status": "error", "error": str(e)}
            
    print(json.dumps(responses, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
