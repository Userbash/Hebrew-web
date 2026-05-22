-- Restore minimum self-service permissions for default user role.
-- This keeps strict admin RBAC controls while allowing normal login flows.

INSERT INTO role_permissions (role_id, permission_id, note)
SELECT r.id, p.id, 'Baseline self-service grant for standard users.'
FROM roles r
JOIN permissions p ON p.permission_name IN (
    'users.read.own',
    'users.update.own',
    'lessons.read.any',
    'quizzes.read.any',
    'quizzes.update.own',
    'dictionary.read.any',
    'progress.read.own'
)
WHERE r.role_key = 'user'
ON CONFLICT (role_id, permission_id) DO UPDATE
SET granted = TRUE,
    note = EXCLUDED.note;
