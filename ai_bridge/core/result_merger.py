from __future__ import annotations

import logging
import uuid
from typing import Any

from .models import AgentResult, ResultEnvelope, ResultPayload, TaskGraph, TaskStatus

logger = logging.getLogger(__name__)

class ResultMerger:
    def merge(self, results: list[AgentResult]) -> dict[str, Any]:
        status = "done" if all(result.status == TaskStatus.DONE for result in results) else "failed"
        files_changed: list[str] = []
        commands_run: list[str] = []
        errors: list[str] = []
        summaries: list[str] = []
        for result in results:
            output = result.output
            summaries.append(str(output.get("summary", "")))
            files_changed.extend(output.get("files_changed", []))
            commands_run.extend(output.get("commands_run", []))
            errors.extend(result.errors)
        return {
            "status": status,
            "summary": " | ".join(s for s in summaries if s),
            "files_changed": sorted(set(files_changed)),
            "commands_run": commands_run,
            "errors": errors,
        }

    def reassemble(self, graph: TaskGraph, results: list[ResultEnvelope]) -> ResultEnvelope:
        """
        Reassembly layer. Correlates results back to the original graph,
        verifies dependencies and acceptance criteria, simulating network packet reassembly.
        """
        logger.info(f"Reassembling results for graph {graph.root_task_id}")
        
        result_map = {res.task_id: res for res in results}
        
        failed_dependencies = set()
        completed_criteria: list[str] = []
        failed_criteria: list[str] = []
        artifacts: list[str] = []
        merged_output: dict[str, Any] = {}
        all_errors: list[str] = []
        
        for node_id, node in graph.nodes.items():
            if node_id not in result_map:
                failed_criteria.append(f"Task {node_id} missing result")
                continue
                
            res = result_map[node_id]
            if res.status == TaskStatus.FAILED:
                failed_dependencies.add(node_id)
                failed_criteria.extend(res.payload.failed_criteria or [f"Task {node_id} failed"])
                all_errors.extend(res.payload.errors)
                continue
                
            for criteria in node.payload.acceptance_criteria:
                if criteria in res.payload.completed_criteria:
                    completed_criteria.append(criteria)
                else:
                    failed_criteria.append(criteria)
                    
            artifacts.extend(res.payload.artifacts)
            merged_output[node_id] = res.payload.output
            
        if failed_dependencies:
            status = TaskStatus.FAILED
            logger.warning(f"Graph {graph.root_task_id} failed due to dependency failures: {failed_dependencies}")
        elif failed_criteria:
            status = TaskStatus.NEEDS_REVIEW
            logger.info(f"Graph {graph.root_task_id} needs review. Failed criteria: {failed_criteria}")
        else:
            status = TaskStatus.DONE
            logger.info(f"Graph {graph.root_task_id} completed successfully.")

        final_payload = ResultPayload(
            task_id=graph.root_task_id,
            status=status,
            output=merged_output,
            artifacts=list(set(artifacts)),
            errors=all_errors,
            warnings=[],
            confidence=1.0 if status == TaskStatus.DONE else 0.5,
            completed_criteria=completed_criteria,
            failed_criteria=failed_criteria
        )
        
        trace_id = results[0].trace_id if results else str(uuid.uuid4())
        corr_id = results[0].correlation_id if results else None
        
        return ResultEnvelope(
            protocol_version="1.0",
            result_id=str(uuid.uuid4()),
            task_id=graph.root_task_id,
            trace_id=trace_id,
            correlation_id=corr_id,
            source_agent="result_merger",
            target_agent=None,
            status=status,
            payload=final_payload
        )
