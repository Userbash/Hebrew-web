import express, { Request, Response } from 'express';
import { verifyToken, RequestWithAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';
import {
  requirePermission,
  requireRole,
} from '../middleware/authorization.js';
import {
  assignRoleToUser,
  listRbacCatalog,
  listUserAssignments,
  revokeRoleFromUser,
  setUserBlockedFlag,
} from '../security/rbacService.js';
import { type RoleKey } from '../security/rbacCatalog.js';
import { db } from '../data/db.js';

const router = express.Router();

const RBAC_ADMIN_ROLES: RoleKey[] = ['root', 'platform_admin'];

const parseRoleKey = (value: unknown): RoleKey => {
  if (typeof value !== 'string') {
    throw new ValidationError('roleKey must be a string');
  }

  const normalized = value.trim() as RoleKey;
  const allowed: RoleKey[] = [
    'root',
    'platform_admin',
    'security_admin',
    'content_admin',
    'editor',
    'moderator',
    'support',
    'analyst',
    'user',
  ];

  if (!allowed.includes(normalized)) {
    throw new ValidationError(`Unknown roleKey: ${value}`);
  }

  return normalized;
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
    const roleKey = parseRoleKey(req.body?.roleKey);
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
    const roleKey = parseRoleKey(req.params.roleKey);
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
