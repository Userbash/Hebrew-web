-- Expand users table for secure registration/login and search optimization

ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS search_vector tsvector;

UPDATE users
SET username = CONCAT(
        regexp_replace(lower(split_part(email, '@', 1)), '[^a-z0-9_.-]', '', 'g'),
        '_',
        substring(id::text, 1, 8)
    )
WHERE username IS NULL OR length(trim(username)) = 0;

ALTER TABLE users ALTER COLUMN username SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'users_username_format_check'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT users_username_format_check
            CHECK (username ~ '^[A-Za-z0-9_.-]{3,50}$');
    END IF;
END $$;

CREATE OR REPLACE FUNCTION users_search_trigger() RETURNS trigger AS $$
begin
  new.search_vector :=
    setweight(to_tsvector('simple', coalesce(new.username,'')), 'A') ||
    setweight(to_tsvector('simple', coalesce(new.email,'')), 'A') ||
    setweight(to_tsvector('simple', coalesce(new.first_name,'')), 'B') ||
    setweight(to_tsvector('simple', coalesce(new.last_name,'')), 'B');
  return new;
end
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_tsvectorupdate ON users;
CREATE TRIGGER users_tsvectorupdate BEFORE INSERT OR UPDATE
ON users FOR EACH ROW EXECUTE FUNCTION users_search_trigger();

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email_lower ON users((lower(email)));
CREATE INDEX IF NOT EXISTS idx_users_registered_at ON users(registered_at);
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);
CREATE INDEX IF NOT EXISTS idx_users_locked_until ON users(locked_until);
CREATE INDEX IF NOT EXISTS idx_users_search ON users USING GIN(search_vector);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique_active
    ON users((lower(username)))
    WHERE deleted_at IS NULL;
