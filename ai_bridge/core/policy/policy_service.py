from .decisions import PolicyDecision
from .risk import risk_level
class PolicyService:
    def decide(self, message: str) -> PolicyDecision:
        r = risk_level(message)
        if r == "high":
            return PolicyDecision(allow=True, require_hitl=True)
        return PolicyDecision(allow=True)
