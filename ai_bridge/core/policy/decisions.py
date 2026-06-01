from pydantic import BaseModel
class PolicyDecision(BaseModel):
    allow: bool = True
    require_hitl: bool = False
    allow_network: bool = False
    allow_filesystem: bool = False
    allow_shell: bool = False
