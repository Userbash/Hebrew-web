CREATE SCHEMA IF NOT EXISTS ai_bridge;

CREATE TABLE IF NOT EXISTS ai_bridge.sessions (
    source_session_id TEXT PRIMARY KEY,
    normalized_session_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_bridge.memories (
    memory_id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    source_session_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    content JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    importance_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_bridge.commands (
    command_id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    source_session_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    command TEXT NOT NULL,
    result JSONB NOT NULL DEFAULT '{}'::jsonb,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    tokens_used BIGINT,
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_bridge.json_themes (
    theme_event_id BIGSERIAL PRIMARY KEY,
    task_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    agent_id TEXT,
    provider TEXT,
    color TEXT,
    status TEXT,
    event_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_bridge_memories_lookup
    ON ai_bridge.memories (session_id, agent_id, memory_type, memory_id DESC);

CREATE INDEX IF NOT EXISTS idx_ai_bridge_memories_key
    ON ai_bridge.memories (session_id, agent_id, memory_type, ((metadata->>'key')), memory_id DESC);

CREATE INDEX IF NOT EXISTS idx_ai_bridge_commands_lookup
    ON ai_bridge.commands (session_id, agent_id, executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_bridge_themes_lookup
    ON ai_bridge.json_themes (session_id, created_at DESC);
