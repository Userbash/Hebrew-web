def extract_task_type(text: str) -> str:
    t = text.lower()
    if "review" in t: return "review"
    if "test" in t: return "test"
    if "doc" in t: return "docs"
    if "fix" in t: return "fix"
    if "plan" in t: return "plan"
    return "code"
