from ai_bridge.core.persistent_memory import PersistentMemoryManager

def test_persistent_memory_manager_init():
    m = PersistentMemoryManager()
    assert m is not None
