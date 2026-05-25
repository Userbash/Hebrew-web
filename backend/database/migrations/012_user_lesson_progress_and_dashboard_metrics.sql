-- User lesson progress state for active/in-progress/completed tracking
CREATE TABLE IF NOT EXISTS user_lesson_progress (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed')),
    progress_percent INTEGER NOT NULL DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, lesson_id)
);

CREATE INDEX IF NOT EXISTS idx_user_lesson_progress_user_status
    ON user_lesson_progress(user_id, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_items_user_acquired_at
    ON user_items(user_id, acquired_at DESC);
