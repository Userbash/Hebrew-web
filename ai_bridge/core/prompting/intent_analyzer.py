def detect_intent(text: str) -> str:
    t = text.lower()
    if "test" in t: return "testing"
    if "fix" in t or "bug" in t: return "fixing"
    if "plan" in t: return "planning"
    return "general"
