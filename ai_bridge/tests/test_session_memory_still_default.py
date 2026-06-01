from ai_bridge.core.session_memory import SessionMemory, MemoryScope

def test_session_memory_still_works():
    mem = SessionMemory()
    mem.set(MemoryScope.SESSION.value, 's1', 'k1', 'v1')
    assert mem.get(MemoryScope.SESSION.value, 's1', 'k1') == 'v1'
