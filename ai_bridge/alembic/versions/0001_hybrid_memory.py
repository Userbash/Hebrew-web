"""hybrid memory phase 1

Revision ID: 0001_hybrid_memory
Revises: 
Create Date: 2026-05-25
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_hybrid_memory"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            parent_agent_id TEXT REFERENCES agents(agent_id),
            type TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            last_active TIMESTAMPTZ,
            status JSONB
        );
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id TEXT REFERENCES agents(agent_id),
            user_id TEXT,
            thread_id TEXT,
            started_at TIMESTAMPTZ DEFAULT NOW(),
            last_updated TIMESTAMPTZ DEFAULT NOW(),
            metadata JSONB
        );
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id BIGSERIAL PRIMARY KEY,
            session_id UUID REFERENCES sessions(session_id),
            agent_id TEXT REFERENCES agents(agent_id),
            memory_type TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR(1536),
            importance_score FLOAT DEFAULT 1.0,
            access_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMPTZ DEFAULT NOW(),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            metadata JSONB,
            expires_at TIMESTAMPTZ
        );
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS command_history (
            id BIGSERIAL PRIMARY KEY,
            session_id UUID REFERENCES sessions,
            agent_id TEXT,
            command TEXT NOT NULL,
            result JSONB,
            success BOOLEAN,
            executed_at TIMESTAMPTZ DEFAULT NOW(),
            tokens_used INTEGER
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_memories_agent_time ON memories(agent_id, last_accessed);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_access ON memories(access_count DESC, last_accessed DESC);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS command_history;")
    op.execute("DROP TABLE IF EXISTS memories;")
    op.execute("DROP TABLE IF EXISTS sessions;")
    op.execute("DROP TABLE IF EXISTS agents;")
