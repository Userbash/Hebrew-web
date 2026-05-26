from __future__ import annotations

import logging
from typing import Any

from .model_selector import ModelSelector, evaluate_risk_context
from .models import (
    ExecutionPlan,
    Priority,
    Task,
    TaskEnvelope,
    TaskGraph,
    TaskInput,
    TaskPayload,
    TaskType,
    encapsulate,
)
from .task_router import CAPABILITY_BY_TASK_TYPE

logger = logging.getLogger(__name__)

class TaskDecomposer:
    def __init__(self, model_selector: ModelSelector | None = None) -> None:
        self.model_selector = model_selector or ModelSelector()

    def decompose(self, task: Task) -> ExecutionPlan:
        if task.type != TaskType.PLAN:
            self._decorate(task)
            return ExecutionPlan(root_task_id=task.task_id, atomic_tasks=[task])

        context = task.context
        description = task.input.description
        plan_priority = task.priority
        review_priority = task.priority if task.priority in {Priority.HIGH, Priority.CRITICAL} else Priority.HIGH
        execution_priority = Priority.NORMAL

        plan = Task(TaskType.PLAN, TaskInput(f"Plan: {description}", acceptance_criteria=["execution plan created"]), context, plan_priority, parent_task_id=task.task_id)
        code = Task(TaskType.CODE, TaskInput(f"Implement: {description}", files=task.input.files, constraints=task.input.constraints, acceptance_criteria=task.input.acceptance_criteria), context, execution_priority, parent_task_id=task.task_id, dependencies=[plan.task_id])
        test = Task(TaskType.TEST, TaskInput(f"Test: {description}", files=task.input.files, acceptance_criteria=["tests pass"]), context, execution_priority, parent_task_id=task.task_id, dependencies=[code.task_id])
        review = Task(TaskType.REVIEW, TaskInput(f"Review: {description}", files=task.input.files, acceptance_criteria=["review pass"]), context, review_priority, parent_task_id=task.task_id, dependencies=[test.task_id])
        tasks = [plan, code, test, review]
        for atomic in tasks:
            self._decorate(atomic)
        return ExecutionPlan(root_task_id=task.task_id, atomic_tasks=tasks)

    def _decorate(self, task: Task) -> None:
        task.required_capability = task.required_capability or CAPABILITY_BY_TASK_TYPE[task.type]
        choice = self.model_selector.select(task)
        task.complexity = choice.complexity
        task.assigned_model = choice.model_name
        task.expected_output = task.expected_output or f"{task.type.value} result matching acceptance criteria"

    def decompose_to_graph(self, envelope: TaskEnvelope) -> TaskGraph:
        """Decompose a high-level task into a DAG of TaskEnvelopes."""
        logger.info(f"Decomposing task {envelope.task_id} into a DAG")
        graph = TaskGraph(root_task_id=envelope.task_id)
        
        base_meta: dict[str, Any] = {
            "trace_id": envelope.trace_id,
            "correlation_id": envelope.correlation_id,
            "priority": envelope.priority,
            "ttl": envelope.ttl,
            "max_hops": envelope.max_hops,
            "security_policy": envelope.security_policy,
            "parent_task_id": envelope.task_id
        }
        
        def create_node(name: str, objective: str, capability: str, dependencies: list[str]) -> TaskEnvelope:
            payload = TaskPayload(
                objective=objective,
                input_data=envelope.payload.input_data,
                context=envelope.payload.context,
                acceptance_criteria=[f"{name} completed successfully"],
                expected_output_format="json",
                artifacts=envelope.payload.artifacts
            )
            meta = base_meta.copy()
            meta["target_capability"] = capability
            meta["dependencies"] = dependencies
            node = encapsulate(payload, meta)
            graph.nodes[node.task_id] = node
            for dep in dependencies:
                if dep not in graph.edges:
                    graph.edges[dep] = []
                graph.edges[dep].append(node.task_id)
            return node
            
        research = create_node("research", f"Research requirements for: {envelope.payload.objective}", "research", [])
        design = create_node("architecture_design", "Design architecture based on research", "plan", [research.task_id])
        
        impl_deps = [design.task_id]
        
        backend = create_node("implementation.backend", "Implement backend components", "code", impl_deps)
        frontend = create_node("implementation.frontend", "Implement frontend components", "code", impl_deps)
        
        test_deps = [backend.task_id, frontend.task_id]
        tests = create_node("implementation.tests", "Write and execute tests", "test", test_deps)
        
        risk = evaluate_risk_context(envelope.payload.objective)
        review_deps = [backend.task_id, frontend.task_id]
        
        if risk.high_risk or envelope.priority in {Priority.HIGH, Priority.CRITICAL}:
            security_review = create_node("security_review", "Perform security review of implementation", "review", review_deps)
            merge_deps = [tests.task_id, security_review.task_id]
        else:
            merge_deps = [tests.task_id]
            
        final_merge = create_node("final_merge", "Merge results and verify acceptance criteria", "plan", merge_deps)
        
        logger.info(f"Generated DAG with {len(graph.nodes)} nodes for task {envelope.task_id}")
        return graph
