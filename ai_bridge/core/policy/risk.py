def risk_level(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["security","secret","auth","database","migration"]):
        return "high"
    return "low"
