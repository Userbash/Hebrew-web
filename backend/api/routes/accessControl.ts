import express, { Request, Response } from 'express';
import { verifyToken, RequestWithAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';
import {
  requirePermission,
  requireRole,
} from '../middleware/authorization.js';
import {
  assignRoleToUser,
  clearAccessProfileCache,
  invalidatePermissionCache,
  listRbacCatalog,
  listUserAssignments,
  revokeRoleFromUser,
  setUserBlockedFlag,
} from '../security/rbacService.js';
import { type RoleKey } from '../security/rbacCatalog.js';
import { db } from '../data/db.js';

const router = express.Router();

const RBAC_ADMIN_ROLES: RoleKey[] = ['root', 'platform_admin'];

const toRoleKey = (value: unknown): RoleKey => {
  if (typeof value !== 'string') {
    throw new ValidationError('roleKey must be a string');
  }

  const normalized = value.trim().toLowerCase().replace(/[^a-z0-9_]+/g, '_').replace(/^_+|_+$/g, '') as RoleKey;
  if (!normalized || normalized.length < 3 || normalized.length > 64) {
    throw new ValidationError('roleKey must be 3-64 chars and contain only a-z, 0-9, _');
  }

  return normalized;
};

const parseRolePriority = (value: unknown) => {
  const parsed = Number.parseInt(String(value ?? ''), 10);
  if (!Number.isFinite(parsed)) {
    return 100;
  }

  return Math.min(5000, Math.max(1, parsed));
};

const normalizeRoleTitle = (value: unknown) => {
  if (typeof value !== 'string' || !value.trim()) {
    throw new ValidationError('title is required');
  }

  return value.trim().slice(0, 120);
};

const normalizeRoleDescription = (value: unknown) => {
  if (typeof value !== 'string') {
    return null;
  }

  const trimmed = value.trim();
  return trimmed ? trimmed.slice(0, 2000) : null;
};

/**
 * GET /api/access/catalog
 * Returns role hierarchy, permission list, and role-permission mapping.
 */
router.get(
  '/catalog',
  verifyToken,
  requirePermission('rbac', 'read', 'any'),
  asyncHandler(async (_req: Request, res: Response) => {
    const catalog = await listRbacCatalog();
    res.status(200).json({ success: true, ...catalog });
  })
);

/**
 * GET /api/access/roles
 * Returns groups (roles) with assignment + permissions counts.
 */
router.get(
  '/roles',
  verifyToken,
  requirePermission('rbac', 'read', 'any'),
  asyncHandler(async (_req: Request, res: Response) => {
    const rolesRes = await db.query(
      `SELECT
          r.id,
          r.management_key,
          r.role_key,
          r.title,
          r.description,
          r.priority,
          r.is_system,
          r.created_at,
          r.updated_at,
          COUNT(DISTINCT rp.permission_id) FILTER (WHERE rp.granted = TRUE)::int AS permissions_count,
          COUNT(DISTINCT ur.id) FILTER (WHERE ur.is_active = TRUE AND ur.revoked_at IS NULL AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP))::int AS assignments_count
       FROM roles r
       LEFT JOIN role_permissions rp ON rp.role_id = r.id
       LEFT JOIN user_roles ur ON ur.role_id = r.id
       GROUP BY r.id
       ORDER BY r.priority DESC, r.role_key ASC`
    );

    res.status(200).json({ success: true, roles: rolesRes.rows, count: rolesRes.rows.length });
  })
);

/**
 * POST /api/access/roles
 * Creates a custom access group (role).
 */
router.post(
  '/roles',
  verifyToken,
  requireRole(RBAC_ADMIN_ROLES),
  requirePermission('rbac', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const title = normalizeRoleTitle(req.body?.title);
    const roleKey = toRoleKey(req.body?.roleKey || title);
    const description = normalizeRoleDescription(req.body?.description);
    const priority = parseRolePriority(req.body?.priority);

    const exists = await db.query('SELECT id FROM roles WHERE role_key = $1 LIMIT 1', [roleKey]);
    if (exists.rows[0]) {
      throw new ValidationError(`Role already exists: ${roleKey}`);
    }

    const created = await db.query(
      `INSERT INTO roles (role_key, title, description, priority, is_system)
       VALUES ($1, $2, $3, $4, FALSE)
       RETURNING id, management_key, role_key, title, description, priority, is_system, created_at, updated_at`,
      [roleKey, title, description, priority]
    );

    invalidatePermissionCache();

    res.status(201).json({
      success: true,
      message: `Group ${roleKey} created`,
      role: created.rows[0],
    });
  })
);

/**
 * PATCH /api/access/roles/:roleKey
 * Updates a custom group.
 */
router.patch(
  '/roles/:roleKey',
  verifyToken,
  requireRole(RBAC_ADMIN_ROLES),
  requirePermission('rbac', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const roleKey = toRoleKey(req.params.roleKey);
    const title = typeof req.body?.title === 'string' ? req.body.title.trim().slice(0, 120) : null;
    const description = typeof req.body?.description === 'string' ? req.body.description.trim().slice(0, 2000) : null;
    const priority = req.body?.priority === undefined ? null : parseRolePriority(req.body?.priority);

    const roleRes = await db.query('SELECT id, role_key, is_system FROM roles WHERE role_key = $1 LIMIT 1', [roleKey]);
    const role = roleRes.rows[0] as { id: string; role_key: string; is_system: boolean } | undefined;
    if (!role) {
      throw new NotFoundError('Role not found');
    }

    if (role.is_system) {
      throw new ValidationError('System roles cannot be edited');
    }

    const updated = await db.query(
      `UPDATE roles
       SET title = COALESCE($1, title),
           description = COALESCE($2, description),
           priority = COALESCE($3, priority),
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $4
       RETURNING id, management_key, role_key, title, description, priority, is_system, created_at, updated_at`,
      [title || null, description, priority, role.id]
    );

    clearAccessProfileCache();

    res.status(200).json({
      success: true,
      message: `Group ${roleKey} updated`,
      role: updated.rows[0],
    });
  })
);

/**
 * DELETE /api/access/roles/:roleKey
 * Deletes a custom group and its assignments.
 */
router.delete(
  '/roles/:roleKey',
  verifyToken,
  requireRole(RBAC_ADMIN_ROLES),
  requirePermission('rbac', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const roleKey = toRoleKey(req.params.roleKey);

    const roleRes = await db.query(
      `SELECT id, is_system
       FROM roles
       WHERE role_key = $1
       LIMIT 1`,
      [roleKey]
    );

    const role = roleRes.rows[0] as { id: string; is_system: boolean } | undefined;
    if (!role) {
      throw new NotFoundError('Role not found');
    }

    if (role.is_system) {
      throw new ValidationError('System roles cannot be deleted');
    }

    await db.query('DELETE FROM roles WHERE id = $1', [role.id]);

    clearAccessProfileCache();
    invalidatePermissionCache();

    res.status(200).json({
      success: true,
      message: `Group ${roleKey} deleted`,
    });
  })
);

/**
 * PUT /api/access/roles/:roleKey/permissions
 * Replaces granted permissions for a group.
 */
router.put(
  '/roles/:roleKey/permissions',
  verifyToken,
  requireRole(RBAC_ADMIN_ROLES),
  requirePermission('rbac', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const roleKey = toRoleKey(req.params.roleKey);
    const permissionNames = Array.isArray(req.body?.permissionNames)
      ? req.body.permissionNames.filter((item: unknown): item is string => typeof item === 'string' && item.trim().length > 0)
      : [];

    const roleRes = await db.query('SELECT id FROM roles WHERE role_key = $1 LIMIT 1', [roleKey]);
    const role = roleRes.rows[0] as { id: string } | undefined;
    if (!role) {
      throw new NotFoundError('Role not found');
    }

    const permissionsRes = await db.query(
      `SELECT id, permission_name
       FROM permissions
       WHERE permission_name = ANY($1::text[])`,
      [permissionNames]
    );

    const foundNames = new Set(permissionsRes.rows.map((row: { permission_name: string }) => row.permission_name));
    const missingNames = permissionNames.filter((name: string) => !foundNames.has(name));

    if (missingNames.length > 0) {
      throw new ValidationError(`Unknown permissions: ${missingNames.join(', ')}`);
    }

    await db.query(
      `UPDATE role_permissions
       SET granted = FALSE,
           note = 'replaced by admin panel',
           created_at = CURRENT_TIMESTAMP
       WHERE role_id = $1`,
      [role.id]
    );

    for (const row of permissionsRes.rows as Array<{ id: string }>) {
      await db.query(
        `INSERT INTO role_permissions (role_id, permission_id, granted, note)
         VALUES ($1, $2, TRUE, 'granted by admin panel')
         ON CONFLICT (role_id, permission_id)
         DO UPDATE SET granted = TRUE, note = EXCLUDED.note`,
        [role.id, row.id]
      );
    }

    clearAccessProfileCache();
    invalidatePermissionCache();

    res.status(200).json({
      success: true,
      message: `Permissions updated for group ${roleKey}`,
      permissionsCount: permissionsRes.rows.length,
    });
  })
);

/**
 * GET /api/access/users/:id
 * Returns RBAC profile and role assignments for a user.
 */
router.get(
  '/users/:id',
  verifyToken,
  requirePermission('rbac', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const targetId = req.params.id;

    const user = await db.getUserById(targetId);
    if (!user) {
      throw new NotFoundError('User not found');
    }

    const result = await listUserAssignments(targetId);
    if (!result) {
      throw new NotFoundError('Access profile not found');
    }

    res.status(200).json({ success: true, ...result });
  })
);

/**
 * POST /api/access/users/:id/roles
 * Assigns a role to a user.
 */
router.post(
  '/users/:id/roles',
  verifyToken,
  requireRole(RBAC_ADMIN_ROLES),
  requirePermission('rbac', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const targetId = req.params.id;
    const roleKey = toRoleKey(req.body?.roleKey);
    const note = typeof req.body?.note === 'string' ? req.body.note : undefined;
    const expiresAt = typeof req.body?.expiresAt === 'string' ? req.body.expiresAt : null;

    const targetUser = await db.getUserById(targetId);
    if (!targetUser) {
      throw new NotFoundError('User not found');
    }

    const updatedProfile = await assignRoleToUser(authReq.userId, targetId, roleKey, note, expiresAt);

    res.status(200).json({
      success: true,
      message: `Role ${roleKey} assigned`,
      profile: updatedProfile,
    });
  })
);

/**
 * DELETE /api/access/users/:id/roles/:roleKey
 * Revokes an active role from user.
 */
router.delete(
  '/users/:id/roles/:roleKey',
  verifyToken,
  requireRole(RBAC_ADMIN_ROLES),
  requirePermission('rbac', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const targetId = req.params.id;
    const roleKey = toRoleKey(req.params.roleKey);
    const note = typeof req.body?.note === 'string' ? req.body.note : undefined;

    const targetUser = await db.getUserById(targetId);
    if (!targetUser) {
      throw new NotFoundError('User not found');
    }

    const updatedProfile = await revokeRoleFromUser(authReq.userId, targetId, roleKey, note);

    res.status(200).json({
      success: true,
      message: `Role ${roleKey} revoked`,
      profile: updatedProfile,
    });
  })
);

/**
 * PATCH /api/access/users/:id/block
 * Sets system-level account block flag.
 */
router.patch(
  '/users/:id/block',
  verifyToken,
  requireRole(RBAC_ADMIN_ROLES),
  requirePermission('users', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const targetId = req.params.id;
    const blocked = Boolean(req.body?.blocked);
    const note = typeof req.body?.note === 'string' ? req.body.note : undefined;

    const targetUser = await db.getUserById(targetId);
    if (!targetUser) {
      throw new NotFoundError('User not found');
    }

    const profile = await setUserBlockedFlag(authReq.userId, targetId, blocked, note);

    res.status(200).json({
      success: true,
      message: blocked ? 'User blocked by policy' : 'User unblocked',
      profile,
    });
  })
);

export default router;
