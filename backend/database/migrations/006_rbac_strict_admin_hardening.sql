-- Strict RBAC hardening.
-- Goal: only administrators can mutate privilege assignments,
-- and newly registered users keep zero effective permissions until admin assignment.

-- 1) Keep rbac.update.any only for root/platform_admin.
DELETE FROM role_permissions rp
USING roles r, permissions p
WHERE rp.role_id = r.id
  AND rp.permission_id = p.id
  AND p.permission_name = 'rbac.update.any'
  AND r.role_key NOT IN ('root', 'platform_admin');

-- 2) Default user role must have zero operational grants.
DELETE FROM role_permissions rp
USING roles r
WHERE rp.role_id = r.id
  AND r.role_key = 'user';

-- 3) Ensure user role exists as a placeholder role even with no grants.
INSERT INTO roles (role_key, title, description, priority, is_system)
VALUES ('user', 'User', 'No default permissions until explicit administrator assignment.', 100, TRUE)
ON CONFLICT (role_key) DO UPDATE
SET title = EXCLUDED.title,
    description = EXCLUDED.description,
    priority = EXCLUDED.priority,
    is_system = EXCLUDED.is_system,
    updated_at = CURRENT_TIMESTAMP;
