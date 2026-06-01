def retrieve(memory_keys: list[str], lookup: dict[str, str]) -> list[str]:
    return [lookup[k] for k in memory_keys if k in lookup]
