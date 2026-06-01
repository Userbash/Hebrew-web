def choose_fallback(primary: str) -> str:
    return "local-small" if primary != "local-small" else "gpt-4o"
