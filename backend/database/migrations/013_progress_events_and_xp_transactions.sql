ALTER TABLE user_lesson_progress
    ADD COLUMN IF NOT EXISTS id BIGSERIAL,
    ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_lesson_progress_id ON user_lesson_progress(id);

CREATE TABLE IF NOT EXISTS user_activity_events (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('lesson_started', 'lesson_completed', 'xp_added', 'lesson_progress_updated')),
    lesson_id UUID NULL REFERENCES items(id) ON DELETE SET NULL,
    xp_delta INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_user_activity_events_user_created
    ON user_activity_events(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS user_xp_transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    reason VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, lesson_id, reason)
);

CREATE INDEX IF NOT EXISTS idx_user_xp_transactions_user_created
    ON user_xp_transactions(user_id, created_at DESC);
