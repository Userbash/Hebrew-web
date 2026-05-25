# AI Bridge Memory Upgrade Plan

Status: Approved
Scope: Memory subsystem, Vector Search, Safety, Reranking
Triggered By: User Orchestrator Directive

## Epic 1: Vector Storage & Hybrid Retrieval (Owner: CodexAgent)
| ID | Task | Agent | DoD |
|---|---|---|---|
| MU-01 | `implement_pgvector_storage` | CodexAgent | pgvector query implemented in `persistent_memory.py` |
| MU-02 | `replace_keyword_matching_with_hybrid_retrieval` | CodexAgent | `HybridMemory.fast_retrieve` supports vector passing |
| MU-03 | `combine_bm25_and_vector_search` | CodexAgent | Full-text search combined with pgvector |
| MU-04 | `add_cross_encoder_reranking` | CodexAgent | Cross-encoder model reranks top-K results |
| MU-05 | `implement_embedding_pipeline` | CodexAgent | Async pipeline for embedding text |
| MU-06 | `use_bge_large_or_e5_large_embeddings` | ExternalAIAgent | Switch to BGE-large/E5-large models |
| MU-07 | `implement_fast_vector_indexing` | CodexAgent | HNSW or IVFFlat indexes tuned |
| MU-08 | `cache_retrieval_results` | CodexAgent | Redis/RAM cache for frequent queries |
| MU-09 | `optimize_large_scale_memory_queries` | CodexAgent | Pagination and cursor support |
| MU-10 | `prepare_architecture_for_million_scale_memory_entries` | PlannerAgent | Sharding and partitioning strategy defined |
| MU-11 | `implement_async_embedding_generation` | CodexAgent | Celery/Asyncio queue for embeddings |
| MU-12 | `analyze_retrieval_bottlenecks` | TesterAgent | Profiling report generated |

## Epic 2: Memory Scoring & Decay Lifecycle (Owner: PlannerAgent & CodexAgent)
| ID | Task | Agent | DoD |
|---|---|---|---|
| MU-13 | `add_memory_confidence_scoring` | CodexAgent | Confidence threshold added to records |
| MU-14 | `track_success_rate_for_memory_items` | CodexAgent | Memory hit/miss tracking metrics |
| MU-15 | `track_last_used_timestamp` | CodexAgent | `last_accessed` used dynamically |
| MU-16 | `implement_memory_decay_system` | CodexAgent | Time-decay formula implemented |
| MU-17 | `ignore_deprecated_memories` | CodexAgent | Hard deprecation flag in DB |
| MU-18 | `prioritize_high_confidence_context` | CodexAgent | Sort by `confidence * decay` |
| MU-19 | `add_background_memory_consolidation` | CodexAgent | Worker task aggregates old memories |

## Epic 3: Memory Structure & Validation (Owner: DocsAgent & ReviewerAgent)
| ID | Task | Agent | DoD |
|---|---|---|---|
| MU-20 | `build_hierarchical_memory_structure` | PlannerAgent | Parent/child memory links |
| MU-21 | `store_summary_episode_and_raw_logs` | CodexAgent | Separation in DB schema |
| MU-22 | `separate_semantic_memory_from_raw_logs` | CodexAgent | Table split: `memories` vs `command_history` |
| MU-23 | `implement_memory_verification_loop` | TesterAgent | Periodic checks for memory drift |
| MU-24 | `validate_memory_against_current_repo_state` | ReviewerAgent | Memory hashed against codebase |
| MU-25 | `detect_architecture_changes_before_context_injection` | ReviewerAgent | AST parsing before injection |
| MU-26 | `prevent_retrieval_context_contamination` | ReviewerAgent | Context boundary enforcement |
| MU-27 | `detect_contradictory_memories` | ExternalAIAgent | LLM pass detects conflicts |
| MU-28 | `implement_memory_deduplication` | CodexAgent | Cosine similarity > 0.98 merged |
| MU-29 | `merge_duplicate_context_entries` | CodexAgent | SQL deduplication script |
| MU-30 | `build_self_healing_memory_system` | PlannerAgent | Self-correction feedback loop |
| MU-31 | `prevent_summary_information_loss` | DocsAgent | Lossless summarization prompts |

## Epic 4: Execution Safety & Context Optimization (Owner: ReviewerAgent & TesterAgent)
| ID | Task | Agent | DoD |
|---|---|---|---|
| MU-32 | `implement_execution_safety_layer` | ReviewerAgent | Interceptor for memory actions |
| MU-33 | `classify_commands_as_safe_confirm_required_dangerous_or_destructive` | ReviewerAgent | Enum and AST validation |
| MU-34 | `block_unsafe_command_replay` | CodexAgent | Execution blocker for replay |
| MU-35 | `prevent_secret_leaks_with_redaction` | ReviewerAgent | Regex/Entropy secret scanner |
| MU-36 | `implement_multi_agent_memory_isolation` | CodexAgent | RLS or namespace isolation |
| MU-37 | `implement_multi_repo_memory_scoping` | CodexAgent | Repo-ID added to tables |
| MU-38 | `add_project_version_metadata` | CodexAgent | Commit SHA tied to memory |
| MU-39 | `add_session_aware_context_filtering` | CodexAgent | Session tag filtering |
| MU-40 | `optimize_context_window_usage` | ExternalAIAgent | Token estimation limits |
| MU-41 | `reduce_prompt_token_bloat` | ExternalAIAgent | YAML/JSON minification |
| MU-42 | `inject_only_relevant_context` | CodexAgent | Threshold-based injection |
| MU-43 | `implement_context_drilldown` | CodexAgent | Lazy-loading of deep context |

## Epic 5: Reasoning and Reflection (Owner: ExternalAIAgent)
| ID | Task | Agent | DoD |
|---|---|---|---|
| MU-44 | `implement_reflection_agents` | ExternalAIAgent | Reflection prompt step |
| MU-45 | `analyze_failed_tasks_and_update_memory` | ExternalAIAgent | Post-mortem generation |
| MU-46 | `improve_agent_reasoning_accuracy` | ExternalAIAgent | Chain-of-thought enforcement |
| MU-47 | `reduce_hallucinations_from_bad_context` | ExternalAIAgent | Hallucination guardrail prompt |
| MU-48 | `improve_semantic_ranking_quality` | TesterAgent | Golden dataset tests |
| MU-49 | `build_production_grade_persistent_ai_memory_system` | PlannerAgent | Sign-off and Release |
