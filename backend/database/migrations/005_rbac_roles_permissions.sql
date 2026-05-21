-- RBAC core schema.
-- Introduces role hierarchy, explicit permission catalog, and user-role assignments.

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    management_key UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
    role_key VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(120) NOT NULL,
    description TEXT,
    priority INTEGER NOT NULL,
    is_system BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    permission_key UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
    permission_name VARCHAR(128) NOT NULL UNIQUE,
    resource VARCHAR(64) NOT NULL,
    action VARCHAR(16) NOT NULL CHECK (action IN ('create', 'read', 'update', 'delete')),
    scope VARCHAR(16) NOT NULL CHECK (scope IN ('own', 'any')),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (resource, action, scope)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    policy_key UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
    granted BOOLEAN NOT NULL DEFAULT TRUE,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_key UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    note TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_roles_priority ON roles(priority DESC);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_active ON user_roles(user_id, is_active, expires_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_roles_unique_active
    ON user_roles(user_id, role_id)
    WHERE is_active = TRUE AND revoked_at IS NULL;

-- Account flags useful for emergency controls and future policies.
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_system_blocked BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS access_labels JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Keep role timestamps in sync.
DROP TRIGGER IF EXISTS update_roles_modtime ON roles;
CREATE TRIGGER update_roles_modtime
BEFORE UPDATE ON roles
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Default role hierarchy from most privileged to least privileged.
INSERT INTO roles (role_key, title, description, priority)
VALUES
    ('root', 'Root', 'Full unrestricted system control, including RBAC management and emergency operations.', 1000),
    ('platform_admin', 'Platform Administrator', 'Global administration of users, content, and configuration except protected root ownership transfer.', 900),
    ('security_admin', 'Security Administrator', 'Manages security controls, lockouts, audit streams, and sensitive user access settings.', 800),
    ('content_admin', 'Content Administrator', 'Manages all lessons, quizzes, dictionary content, and publication lifecycle.', 700),
    ('editor', 'Editor', 'Creates and updates educational content and publications within assigned scope.', 600),
    ('moderator', 'Moderator', 'Moderates user-generated content and can hide or remove policy-violating records.', 500),
    ('support', 'Support Specialist', 'Can inspect users and progress to assist with operational issues without destructive rights.', 400),
    ('analyst', 'Analyst', 'Read-only access to telemetry, reports, and health metrics.', 300),
    ('user', 'User', 'Standard product user with self-service profile and learning actions.', 100)
ON CONFLICT (role_key) DO NOTHING;

-- Permission catalog. This list is intentionally explicit for auditability.
INSERT INTO permissions (permission_name, resource, action, scope, description)
VALUES
    ('system.read.any', 'system', 'read', 'any', 'View system configuration and health metadata.'),
    ('system.update.any', 'system', 'update', 'any', 'Modify global system configuration and feature flags.'),

    ('rbac.read.any', 'rbac', 'read', 'any', 'Inspect role, permission, and assignment graph.'),
    ('rbac.update.any', 'rbac', 'update', 'any', 'Grant, revoke, or change role assignments and role policies.'),

    ('users.create.any', 'users', 'create', 'any', 'Create user accounts administratively.'),
    ('users.read.any', 'users', 'read', 'any', 'Read full user profiles and account state.'),
    ('users.update.any', 'users', 'update', 'any', 'Update any user profile and status fields.'),
    ('users.delete.any', 'users', 'delete', 'any', 'Soft-delete or purge user accounts.'),
    ('users.read.own', 'users', 'read', 'own', 'Read own profile.'),
    ('users.update.own', 'users', 'update', 'own', 'Update own profile.'),

    ('lessons.create.any', 'lessons', 'create', 'any', 'Create lessons globally.'),
    ('lessons.read.any', 'lessons', 'read', 'any', 'Read lessons globally.'),
    ('lessons.update.any', 'lessons', 'update', 'any', 'Edit lessons globally.'),
    ('lessons.delete.any', 'lessons', 'delete', 'any', 'Delete lessons globally.'),

    ('quizzes.create.any', 'quizzes', 'create', 'any', 'Create quizzes globally.'),
    ('quizzes.read.any', 'quizzes', 'read', 'any', 'Read quizzes globally.'),
    ('quizzes.update.any', 'quizzes', 'update', 'any', 'Edit quizzes globally.'),
    ('quizzes.delete.any', 'quizzes', 'delete', 'any', 'Delete quizzes globally.'),
    ('quizzes.update.own', 'quizzes', 'update', 'own', 'Submit own quiz attempts.'),

    ('dictionary.read.any', 'dictionary', 'read', 'any', 'Read dictionary entries.'),
    ('dictionary.create.any', 'dictionary', 'create', 'any', 'Create dictionary entries.'),
    ('dictionary.update.any', 'dictionary', 'update', 'any', 'Update dictionary entries.'),
    ('dictionary.delete.any', 'dictionary', 'delete', 'any', 'Delete dictionary entries.'),

    ('items.read.any', 'items', 'read', 'any', 'Read generic item records.'),
    ('items.create.any', 'items', 'create', 'any', 'Create generic item records.'),
    ('items.update.any', 'items', 'update', 'any', 'Update generic item records.'),
    ('items.delete.any', 'items', 'delete', 'any', 'Delete generic item records.'),

    ('progress.read.any', 'progress', 'read', 'any', 'Read any user progress.'),
    ('progress.read.own', 'progress', 'read', 'own', 'Read own progress.'),

    ('telemetry.read.any', 'telemetry', 'read', 'any', 'Read telemetry and audit streams.'),
    ('telemetry.delete.any', 'telemetry', 'delete', 'any', 'Prune telemetry and audit records.'),

    ('publications.create.any', 'publications', 'create', 'any', 'Create publication entities.'),
    ('publications.read.any', 'publications', 'read', 'any', 'Read publication entities.'),
    ('publications.update.any', 'publications', 'update', 'any', 'Update publication entities.'),
    ('publications.delete.any', 'publications', 'delete', 'any', 'Delete publication entities.'),
    ('publications.create.own', 'publications', 'create', 'own', 'Create own publication drafts.'),
    ('publications.read.own', 'publications', 'read', 'own', 'Read own publication drafts.'),
    ('publications.update.own', 'publications', 'update', 'own', 'Update own publication drafts.'),
    ('publications.delete.own', 'publications', 'delete', 'own', 'Delete own publication drafts.')
ON CONFLICT (permission_name) DO NOTHING;

-- Role -> permission mapping by hierarchy.
-- Root receives all permissions automatically.
INSERT INTO role_permissions (role_id, permission_id, note)
SELECT r.id, p.id, 'Root has full authority.'
FROM roles r
CROSS JOIN permissions p
WHERE r.role_key = 'root'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id, note)
SELECT r.id, p.id, 'Platform admin operational scope.'
FROM roles r
JOIN permissions p ON p.permission_name IN (
    'system.read.any', 'system.update.any',
    'rbac.read.any', 'rbac.update.any',
    'users.create.any', 'users.read.any', 'users.update.any', 'users.delete.any',
    'lessons.create.any', 'lessons.read.any', 'lessons.update.any', 'lessons.delete.any',
    'quizzes.create.any', 'quizzes.read.any', 'quizzes.update.any', 'quizzes.delete.any',
    'dictionary.read.any', 'dictionary.create.any', 'dictionary.update.any', 'dictionary.delete.any',
    'items.read.any', 'items.create.any', 'items.update.any', 'items.delete.any',
    'progress.read.any',
    'telemetry.read.any', 'telemetry.delete.any',
    'publications.create.any', 'publications.read.any', 'publications.update.any', 'publications.delete.any'
)
WHERE r.role_key = 'platform_admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id, note)
SELECT r.id, p.id, 'Security administration scope.'
FROM roles r
JOIN permissions p ON p.permission_name IN (
    'system.read.any',
    'rbac.read.any', 'rbac.update.any',
    'users.read.any', 'users.update.any',
    'telemetry.read.any', 'telemetry.delete.any',
    'progress.read.any'
)
WHERE r.role_key = 'security_admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id, note)
SELECT r.id, p.id, 'Content administration scope.'
FROM roles r
JOIN permissions p ON p.permission_name IN (
    'lessons.create.any', 'lessons.read.any', 'lessons.update.any', 'lessons.delete.any',
    'quizzes.create.any', 'quizzes.read.any', 'quizzes.update.any', 'quizzes.delete.any',
    'dictionary.read.any', 'dictionary.create.any', 'dictionary.update.any', 'dictionary.delete.any',
    'items.read.any', 'items.create.any', 'items.update.any', 'items.delete.any',
    'publications.create.any', 'publications.read.any', 'publications.update.any', 'publications.delete.any',
    'progress.read.any'
)
WHERE r.role_key = 'content_admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id, note)
SELECT r.id, p.id, 'Editor scope.'
FROM roles r
JOIN permissions p ON p.permission_name IN (
    'lessons.read.any', 'lessons.update.any',
    'quizzes.read.any', 'quizzes.update.any',
    'dictionary.read.any',
    'publications.create.own', 'publications.read.own', 'publications.update.own', 'publications.delete.own'
)
WHERE r.role_key = 'editor'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id, note)
SELECT r.id, p.id, 'Moderator scope.'
FROM roles r
JOIN permissions p ON p.permission_name IN (
    'users.read.any',
    'publications.read.any', 'publications.update.any',
    'dictionary.read.any',
    'progress.read.any'
)
WHERE r.role_key = 'moderator'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id, note)
SELECT r.id, p.id, 'Support scope.'
FROM roles r
JOIN permissions p ON p.permission_name IN (
    'users.read.any', 'users.update.any',
    'progress.read.any',
    'lessons.read.any', 'quizzes.read.any', 'dictionary.read.any'
)
WHERE r.role_key = 'support'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id, note)
SELECT r.id, p.id, 'Analyst scope.'
FROM roles r
JOIN permissions p ON p.permission_name IN (
    'system.read.any',
    'progress.read.any',
    'telemetry.read.any',
    'users.read.any'
)
WHERE r.role_key = 'analyst'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id, note)
SELECT r.id, p.id, 'Default end-user scope.'
FROM roles r
JOIN permissions p ON p.permission_name IN (
    'users.read.own', 'users.update.own',
    'lessons.read.any', 'quizzes.read.any',
    'quizzes.update.own',
    'dictionary.read.any',
    'progress.read.own',
    'publications.create.own', 'publications.read.own', 'publications.update.own', 'publications.delete.own'
)
WHERE r.role_key = 'user'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Backfill user_roles from legacy users.role field.
INSERT INTO user_roles (user_id, role_id, note, is_active)
SELECT u.id, r.id, 'Backfilled from legacy users.role', TRUE
FROM users u
JOIN roles r ON r.role_key = CASE
    WHEN lower(u.role) = 'admin' THEN 'platform_admin'
    WHEN lower(u.role) = 'moderator' THEN 'moderator'
    ELSE 'user'
END
LEFT JOIN user_roles ur
    ON ur.user_id = u.id
   AND ur.role_id = r.id
   AND ur.is_active = TRUE
   AND ur.revoked_at IS NULL
WHERE ur.id IS NULL;
