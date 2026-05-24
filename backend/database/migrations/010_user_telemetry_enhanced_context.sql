-- Expand user_telemetry with richer user/session/auth context
-- to track who did what, from where, and in which account state.

ALTER TABLE user_telemetry
    ADD COLUMN IF NOT EXISTS session_id UUID,
    ADD COLUMN IF NOT EXISTS area VARCHAR(32) NOT NULL DEFAULT 'site',
    ADD COLUMN IF NOT EXISTS resource VARCHAR(96) NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS action VARCHAR(64) NOT NULL DEFAULT 'request',
    ADD COLUMN IF NOT EXISTS outcome VARCHAR(16) NOT NULL DEFAULT 'success',
    ADD COLUMN IF NOT EXISTS target_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS is_authenticated BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS login_identifier VARCHAR(255),
    ADD COLUMN IF NOT EXISTS user_role VARCHAR(64),
    ADD COLUMN IF NOT EXISTS highest_role VARCHAR(64),
    ADD COLUMN IF NOT EXISTS role_keys TEXT[] NOT NULL DEFAULT ARRAY[]::text[],
    ADD COLUMN IF NOT EXISTS is_system_blocked BOOLEAN,
    ADD COLUMN IF NOT EXISTS had_previous_login BOOLEAN,
    ADD COLUMN IF NOT EXISTS account_locked BOOLEAN,
    ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'user_telemetry_outcome_check'
    ) THEN
        ALTER TABLE user_telemetry
            ADD CONSTRAINT user_telemetry_outcome_check
            CHECK (outcome IN ('success', 'error', 'blocked'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_user_telemetry_area_action_created
    ON user_telemetry(area, resource, action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_telemetry_outcome_created
    ON user_telemetry(outcome, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_telemetry_target_user_created
    ON user_telemetry(target_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_telemetry_login_identifier_created
    ON user_telemetry((lower(login_identifier)), created_at DESC)
    WHERE login_identifier IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_user_telemetry_role_created
    ON user_telemetry(user_role, highest_role, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_telemetry_auth_state_created
    ON user_telemetry(is_authenticated, is_system_blocked, account_locked, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_telemetry_metadata_gin
    ON user_telemetry USING GIN(metadata);
