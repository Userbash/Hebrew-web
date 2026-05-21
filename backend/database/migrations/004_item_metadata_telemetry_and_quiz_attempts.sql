-- Add item metadata, telemetry storage, and quiz attempts tracking.
-- This migration is idempotent and safe to run on existing databases.

ALTER TABLE items
    ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_items_category_metadata_difficulty
    ON items (category, (metadata->>'difficulty'));

CREATE INDEX IF NOT EXISTS idx_items_category_metadata_lesson_id
    ON items (category, (metadata->>'lessonId'));

CREATE TABLE IF NOT EXISTS user_telemetry (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    method VARCHAR(16) NOT NULL,
    path TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    ip_address VARCHAR(128),
    user_agent TEXT,
    response_time_ms INTEGER NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_telemetry_user_id ON user_telemetry(user_id);
CREATE INDEX IF NOT EXISTS idx_user_telemetry_created_at ON user_telemetry(created_at DESC);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    answers JSONB NOT NULL,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_quiz_submitted
    ON quiz_attempts(user_id, quiz_id, submitted_at DESC);
