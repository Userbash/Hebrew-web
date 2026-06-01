from ai_bridge.adapters.memory.postgres_memory_store import PostgresMemoryShadowStore
from ai_bridge.core.session_memory import SessionMemory, MemoryScope

def test_shadow_write_does_not_break_existing_memory():
    mem = SessionMemory()
    shadow = PostgresMemoryShadowStore(mem)
    shadow.set(MemoryScope.SESSION.value, 's1', 'k', 'v')
    assert shadow.get(MemoryScope.SESSION.value, 's1', 'k') == 'v'
