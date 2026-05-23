import pytest
from ai_bridge.core.models import TaskPayload, encapsulate
from ai_bridge.core.task_decomposer import TaskDecomposer

def test_dag_decomposition():
    payload = TaskPayload(
        objective="Build a new login system",
        input_data={},
        context={},
        acceptance_criteria=["Works securely"],
        expected_output_format="code",
        artifacts=["auth.py"]
    )
    
    # Simulate a high priority task which triggers security review
    envelope = encapsulate(payload, {"priority": "critical"})
    
    decomposer = TaskDecomposer()
    graph = decomposer.decompose_to_graph(envelope)
    
    assert graph.root_task_id == envelope.task_id
    assert len(graph.nodes) == 7 # research, design, backend, frontend, tests, security, merge
    
    # Check dependencies
    nodes_by_cap = {node.target_capability: node for node in graph.nodes.values()}
    assert "research" in nodes_by_cap
    assert "plan" in nodes_by_cap
    assert "code" in nodes_by_cap
    assert "test" in nodes_by_cap
    assert "review" in nodes_by_cap
    
    # Backend and frontend should both depend on design
    # But since their names are specific, we can inspect payload objectives
    nodes_by_obj = {node.payload.objective: node for node in graph.nodes.values()}
    backend_node = nodes_by_obj["Implement backend components"]
    frontend_node = nodes_by_obj["Implement frontend components"]
    design_node = nodes_by_obj["Design architecture based on research"]
    
    assert design_node.task_id in backend_node.dependencies
    assert design_node.task_id in frontend_node.dependencies
