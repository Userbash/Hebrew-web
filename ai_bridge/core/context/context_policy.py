def should_compress(token_count: int, window: int) -> bool:
    return token_count > int(window * 0.75)
