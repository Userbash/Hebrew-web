#!/usr/bin/env bash
set -euo pipefail

mkdir -p .agent/tasks

# Array of all 49 tasks from the backlog
TASKS=(
    "MU-01:implement_pgvector_storage:ai_bridge/core/persistent_memory.py"
    "MU-02:replace_keyword_matching_with_hybrid_retrieval:ai_bridge/core/hybrid_memory.py"
    "MU-03:combine_bm25_and_vector_search:ai_bridge/core/persistent_memory.py"
    "MU-04:add_cross_encoder_reranking:ai_bridge/core/hybrid_memory.py"
    "MU-05:implement_embedding_pipeline:ai_bridge/core/hybrid_memory.py"
    "MU-06:use_bge_large_or_e5_large_embeddings:ai_bridge/core/orchestrator.py"
    "MU-07:implement_fast_vector_indexing:ai_bridge/alembic/versions/0001_hybrid_memory.py"
    "MU-08:cache_retrieval_results:ai_bridge/core/hybrid_memory.py"
    "MU-09:optimize_large_scale_memory_queries:ai_bridge/core/persistent_memory.py"
    "MU-10:prepare_architecture_for_million_scale_memory_entries:docs/AI_BRIDGE_MEMORY_UPGRADE_PLAN.md"
    "MU-11:implement_async_embedding_generation:ai_bridge/core/hybrid_memory.py"
    "MU-12:analyze_retrieval_bottlenecks:tests/system/memory_profiler.py"
    "MU-13:add_memory_confidence_scoring:ai_bridge/core/models.py"
    "MU-14:track_success_rate_for_memory_items:ai_bridge/core/metrics.py"
    "MU-15:track_last_used_timestamp:ai_bridge/core/persistent_memory.py"
    "MU-16:implement_memory_decay_system:ai_bridge/core/hybrid_memory.py"
    "MU-17:ignore_deprecated_memories:ai_bridge/core/persistent_memory.py"
    "MU-18:prioritize_high_confidence_context:ai_bridge/core/hybrid_memory.py"
    "MU-19:add_background_memory_consolidation:ai_bridge/core/memory_consolidator.py"
    "MU-20:build_hierarchical_memory_structure:docs/AI_BRIDGE_SESSION_MEMORY.md"
    "MU-21:store_summary_episode_and_raw_logs:ai_bridge/core/persistent_memory.py"
    "MU-22:separate_semantic_memory_from_raw_logs:ai_bridge/alembic/versions/0001_hybrid_memory.py"
    "MU-23:implement_memory_verification_loop:ai_bridge/core/orchestrator.py"
    "MU-24:validate_memory_against_current_repo_state:ai_bridge/core/hybrid_memory.py"
    "MU-25:detect_architecture_changes_before_context_injection:ai_bridge/core/task_router.py"
    "MU-26:prevent_retrieval_context_contamination:ai_bridge/core/hybrid_memory.py"
    "MU-27:detect_contradictory_memories:ai_bridge/core/external_ai_bridge.py"
    "MU-28:implement_memory_deduplication:ai_bridge/core/persistent_memory.py"
    "MU-29:merge_duplicate_context_entries:ai_bridge/core/persistent_memory.py"
    "MU-30:build_self_healing_memory_system:ai_bridge/core/orchestrator.py"
    "MU-31:prevent_summary_information_loss:ai_bridge/core/memory_consolidator.py"
    "MU-32:implement_execution_safety_layer:ai_bridge/core/security.py"
    "MU-33:classify_commands_as_safe_confirm_required_dangerous_or_destructive:ai_bridge/core/security_gate/command_classifier.py"
    "MU-34:block_unsafe_command_replay:ai_bridge/core/security.py"
    "MU-35:prevent_secret_leaks_with_redaction:ai_bridge/core/memory_policy.py"
    "MU-36:implement_multi_agent_memory_isolation:ai_bridge/core/persistent_memory.py"
    "MU-37:implement_multi_repo_memory_scoping:ai_bridge/core/persistent_memory.py"
    "MU-38:add_project_version_metadata:ai_bridge/core/models.py"
    "MU-39:add_session_aware_context_filtering:ai_bridge/core/persistent_memory.py"
    "MU-40:optimize_context_window_usage:ai_bridge/core/hybrid_memory.py"
    "MU-41:reduce_prompt_token_bloat:ai_bridge/core/external_ai_bridge.py"
    "MU-42:inject_only_relevant_context:ai_bridge/core/orchestrator.py"
    "MU-43:implement_context_drilldown:ai_bridge/core/hybrid_memory.py"
    "MU-44:implement_reflection_agents:ai_bridge/agents/external_ai_agent.py"
    "MU-45:analyze_failed_tasks_and_update_memory:ai_bridge/core/feedback_loop.py"
    "MU-46:improve_agent_reasoning_accuracy:ai_bridge/agents/gemini_cli_agent.py"
    "MU-47:reduce_hallucinations_from_bad_context:ai_bridge/agents/mistral_agent.py"
    "MU-48:improve_semantic_ranking_quality:ai_bridge/core/quality_analyzer.py"
    "MU-49:build_production_grade_persistent_ai_memory_system:docs/AI_BRIDGE_ARCHITECTURE.md"
)

echo "Orchestrator: Queuing ${#TASKS[@]} tasks for execution..."

for item in "${TASKS[@]}"; do
    ID=$(echo "$item" | cut -d':' -f1)
    DESC=$(echo "$item" | cut -d':' -f2 | tr '_' ' ')
    FILE=$(echo "$item" | cut -d':' -f3)
    
    # We call the existing script to queue the task for agents
    bash scripts/create-gemini-task.sh "$ID" "$FILE" "IMPLEMENT: $DESC" > /dev/null
done

echo "Orchestrator: All tasks have been decomposed and stored in .agent/tasks/"
