ALTER TABLE users
    ADD COLUMN IF NOT EXISTS ui_preferences JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_users_ui_preferences_gin
    ON users USING GIN (ui_preferences);
