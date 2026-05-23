import pytest
from ai_bridge.core.models import (
    TaskPayload, TaskEnvelope, TaskGraph, ResultPayload, ResultEnvelope, TaskStatus
)
from ai_bridge.core.result_merger import ResultMerger

def test_reassemble_success():
    merger = ResultMerger()
    graph = TaskGraph(root_task_id="root-1")
    
    # Setup graph
    t1 = TaskEnvelope("1.0", "t1", "root-1", "trace", None, "sys", None, "any", "normal", "qos", 3600, None, 0, 10, 0, 3, None, "global", [], TaskPayload("obj", {}, {}, ["crit1"], "json", []))
    t2 = TaskEnvelope("1.0", "t2", "root-1", "trace", None, "sys", None, "any", "normal", "qos", 3600, None, 0, 10, 0, 3, None, "global", [], TaskPayload("obj", {}, {}, ["crit2"], "json", []))
    graph.nodes = {"t1": t1, "t2": t2}
    
    # Setup results
    r1 = ResultEnvelope("1.0", "r1", "t1", "trace", None, "sys", None, TaskStatus.DONE, ResultPayload("t1", TaskStatus.DONE, {}, [], [], [], 1.0, ["crit1"], []))
    r2 = ResultEnvelope("1.0", "r2", "t2", "trace", None, "sys", None, TaskStatus.DONE, ResultPayload("t2", TaskStatus.DONE, {}, [], [], [], 1.0, ["crit2"], []))
    
    final_result = merger.reassemble(graph, [r1, r2])
    assert final_result.status == TaskStatus.DONE
    assert len(final_result.payload.completed_criteria) == 2

def test_reassemble_missing_criteria():
    merger = ResultMerger()
    graph = TaskGraph(root_task_id="root-1")
    
    t1 = TaskEnvelope("1.0", "t1", "root-1", "trace", None, "sys", None, "any", "normal", "qos", 3600, None, 0, 10, 0, 3, None, "global", [], TaskPayload("obj", {}, {}, ["crit1"], "json", []))
    graph.nodes = {"t1": t1}
    
    r1 = ResultEnvelope("1.0", "r1", "t1", "trace", None, "sys", None, TaskStatus.DONE, ResultPayload("t1", TaskStatus.DONE, {}, [], [], [], 1.0, [], []))
    
    final_result = merger.reassemble(graph, [r1])
    assert final_result.status == TaskStatus.NEEDS_REVIEW
    assert "crit1" in final_result.payload.failed_criteria

def test_reassemble_failed_dependency():
    merger = ResultMerger()
    graph = TaskGraph(root_task_id="root-1")
    
    t1 = TaskEnvelope("1.0", "t1", "root-1", "trace", None, "sys", None, "any", "normal", "qos", 3600, None, 0, 10, 0, 3, None, "global", [], TaskPayload("obj", {}, {}, ["crit1"], "json", []))
    graph.nodes = {"t1": t1}
    
    r1 = ResultEnvelope("1.0", "r1", "t1", "trace", None, "sys", None, TaskStatus.FAILED, ResultPayload("t1", TaskStatus.FAILED, {}, [], ["error"], [], 0.0, [], ["failed"]))
    
    final_result = merger.reassemble(graph, [r1])
    assert final_result.status == TaskStatus.FAILED
    assert "error" in final_result.payload.errors
