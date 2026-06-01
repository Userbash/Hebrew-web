def summarize(chunks: list[str], max_chars: int = 2000) -> str:
    return "\n".join(chunks)[:max_chars]
