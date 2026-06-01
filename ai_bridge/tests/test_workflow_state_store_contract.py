from ai_bridge.adapters.state.memory_state_store import MemoryWorkflowStateStore

def test_memory_state_store_contract():
    store = MemoryWorkflowStateStore()
    store.save_workflow('wf1', {'status': 'running'})
    store.append_event('wf1', 'task.received', {'ok': True})
    assert store.get_workflow('wf1') == {'status': 'running'}
