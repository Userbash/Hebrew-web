from pydantic import BaseModel
class NormalizedPrompt(BaseModel):
    original_text: str
    cleaned_text: str
    user_intent: str
    task_type: str
    constraints: list[str] = []
    required_agents: list[str] = []
    required_tools: list[str] = []
    output_format: str = "text"
    risk_level: str = "low"
    memory_references: list[str] = []
    context_requirements: list[str] = []
