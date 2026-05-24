-- Admin search acceleration indexes.
-- Focuses on the new user list filters (RBAC, permissions, publication linkage).

CREATE INDEX IF NOT EXISTS idx_users_created_at_desc ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_last_login_desc ON users(last_login DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_user_roles_active_role_user
    ON user_roles(role_id, user_id)
    WHERE is_active = TRUE AND revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_role_permissions_role_granted
    ON role_permissions(role_id, granted)
    WHERE granted = TRUE;

CREATE INDEX IF NOT EXISTS idx_items_publication_author_id
    ON items((metadata->>'authorId'))
    WHERE category = 'publication';

CREATE INDEX IF NOT EXISTS idx_items_publication_author_status
    ON items((metadata->>'authorId'), (COALESCE(metadata->>'status', 'draft')))
    WHERE category = 'publication';

CREATE INDEX IF NOT EXISTS idx_items_publication_text_search
    ON items USING GIN (to_tsvector('simple', COALESCE(name, '') || ' ' || COALESCE(description, '')))
    WHERE category = 'publication';
