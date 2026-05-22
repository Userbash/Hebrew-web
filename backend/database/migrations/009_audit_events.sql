-- Global audit trail for site and admin mutations.
-- Captures who changed what, where, when, and with which outcome.

CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    event_key UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID,
    area VARCHAR(32) NOT NULL,
    resource VARCHAR(96) NOT NULL,
    action VARCHAR(64) NOT NULL,
    outcome VARCHAR(16) NOT NULL CHECK (outcome IN ('success', 'error', 'blocked')),
    method VARCHAR(10) NOT NULL,
    path TEXT NOT NULL,
    target_type VARCHAR(64),
    target_id TEXT,
    status_code INTEGER NOT NULL,
    ip_address VARCHAR(64),
    user_agent TEXT,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_events_created_at_desc
    ON audit_events(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_events_actor_created_at
    ON audit_events(actor_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_events_area_resource_action
    ON audit_events(area, resource, action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_events_outcome_status
    ON audit_events(outcome, status_code, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_events_target
    ON audit_events(target_type, target_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_events_metadata_gin
    ON audit_events USING GIN(metadata);
