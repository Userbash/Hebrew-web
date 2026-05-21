import { db } from '../data/db.js';
import {
  buildAccessControl,
  roleFromLegacy,
  ROLE_PRIORITY,
  ROLE_PRIVILEGES_OVERVIEW,
  type CrudAction,
  type PermissionScope,
  type RbacResource,
  type RoleKey,
} from './rbacCatalog.js';
import {
  assertBlockMutationAllowed,
  assertRoleMutationAllowed,
  sanitizeGovernanceNote,
} from './rbacGovernance.js';

const accessControl = buildAccessControl();

interface AccessProfileRow {
  user_id: string;
  legacy_role: string;
  is_system_blocked: boolean;
  role_keys: string[] | null;
}

export interface UserAccessProfile {
  userId: string;
  roleKeys: RoleKey[];
  highestRole: RoleKey;
  highestPriority: number;
  isSystemBlocked: boolean;
}

const profileCache = new Map<string, { expiresAt: number; value: UserAccessProfile }>();
const PROFILE_CACHE_TTL_MS = 15_000;

const normalizeRoles = (roles: string[] | null, legacyRole: string): RoleKey[] => {
  const normalized = new Set<RoleKey>();

  for (const role of roles || []) {
    if (role in ROLE_PRIORITY) {
      normalized.add(role as RoleKey);
    }
  }

  // Keep legacy fallback for migration-safe startup.
  // `user` role has no default grants, so new registrations still remain restricted.
  if (normalized.size === 0) {
    normalized.add(roleFromLegacy(legacyRole));
  }

  return Array.from(normalized).sort((a, b) => ROLE_PRIORITY[b] - ROLE_PRIORITY[a]);
};

const highestRoleOf = (roles: RoleKey[]): RoleKey => {
  return roles[0] || 'user';
};

const normalizeExpiresAt = (value?: string | null) => {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    throw new Error('expiresAt must be a valid ISO date-time string');
  }

  if (parsed.getTime() <= Date.now()) {
    throw new Error('expiresAt must be in the future');
  }

  return parsed.toISOString();
};

export const clearAccessProfileCache = (userId?: string) => {
  if (userId) {
    profileCache.delete(userId);
    return;
  }

  profileCache.clear();
};

export const getUserAccessProfile = async (userId: string): Promise<UserAccessProfile | null> => {
  const cached = profileCache.get(userId);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.value;
  }

  const res = await db.query(
    `SELECT
        u.id AS user_id,
        u.role AS legacy_role,
        u.is_system_blocked,
        COALESCE(
          ARRAY_AGG(r.role_key ORDER BY r.priority DESC)
            FILTER (WHERE ur.is_active = TRUE AND ur.revoked_at IS NULL AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)),
          ARRAY[]::text[]
        ) AS role_keys
      FROM users u
      LEFT JOIN user_roles ur ON ur.user_id = u.id
      LEFT JOIN roles r ON r.id = ur.role_id
      WHERE u.id = $1 AND u.deleted_at IS NULL
      GROUP BY u.id, u.role, u.is_system_blocked`,
    [userId]
  );

  const row = res.rows[0] as AccessProfileRow | undefined;
  if (!row) {
    return null;
  }

  const roleKeys = normalizeRoles(row.role_keys, row.legacy_role);
  const highestRole = highestRoleOf(roleKeys);

  const profile: UserAccessProfile = {
    userId,
    roleKeys,
    highestRole,
    highestPriority: ROLE_PRIORITY[highestRole],
    isSystemBlocked: Boolean(row.is_system_blocked),
  };

  profileCache.set(userId, {
    value: profile,
    expiresAt: Date.now() + PROFILE_CACHE_TTL_MS,
  });

  return profile;
};

export const canAccess = (
  roles: RoleKey[],
  action: CrudAction,
  scope: PermissionScope,
  resource: RbacResource
) => {
  for (const role of roles) {
    const permission = accessControl.permission({
      role,
      action: `${action}:${scope}`,
      resource,
    });

    if (permission.granted) {
      return true;
    }
  }

  return false;
};

export const listRbacCatalog = async () => {
  const rolesRes = await db.query(
    `SELECT id, management_key, role_key, title, description, priority, is_system, created_at, updated_at
     FROM roles
     ORDER BY priority DESC`
  );

  const permissionsRes = await db.query(
    `SELECT id, permission_key, permission_name, resource, action, scope, description, created_at
     FROM permissions
     ORDER BY resource, action, scope`
  );

  const rolePermissionsRes = await db.query(
    `SELECT
        r.role_key,
        p.permission_name,
        p.resource,
        p.action,
        p.scope,
        rp.granted,
        rp.policy_key,
        rp.note
     FROM role_permissions rp
     JOIN roles r ON r.id = rp.role_id
     JOIN permissions p ON p.id = rp.permission_id
     ORDER BY r.priority DESC, p.resource, p.action, p.scope`
  );

  return {
    hierarchy: ROLE_PRIVILEGES_OVERVIEW,
    roles: rolesRes.rows,
    permissions: permissionsRes.rows,
    rolePermissions: rolePermissionsRes.rows,
  };
};

export const listUserAssignments = async (userId: string) => {
  const profile = await getUserAccessProfile(userId);
  if (!profile) {
    return null;
  }

  const assignmentsRes = await db.query(
    `SELECT
        ur.id,
        ur.assignment_key,
        ur.note,
        ur.is_active,
        ur.assigned_at,
        ur.expires_at,
        ur.revoked_at,
        ur.assigned_by,
        r.role_key,
        r.title,
        r.priority
     FROM user_roles ur
     JOIN roles r ON r.id = ur.role_id
     WHERE ur.user_id = $1
     ORDER BY ur.assigned_at DESC`,
    [userId]
  );

  return {
    profile,
    assignments: assignmentsRes.rows,
  };
};

export const assignRoleToUser = async (
  actorId: string,
  targetUserId: string,
  roleKey: RoleKey,
  note?: string,
  expiresAt?: string | null
) => {
  const roleRes = await db.query('SELECT id, priority FROM roles WHERE role_key = $1 LIMIT 1', [roleKey]);
  const role = roleRes.rows[0] as { id: string; priority: number } | undefined;
  if (!role) {
    throw new Error(`Role not found: ${roleKey}`);
  }

  const actorProfile = await getUserAccessProfile(actorId);
  const targetProfile = await getUserAccessProfile(targetUserId);

  if (!actorProfile || !targetProfile) {
    throw new Error('Actor or target not found');
  }

  assertRoleMutationAllowed({
    actor: actorProfile,
    target: targetProfile,
    targetRoleKey: roleKey,
    mutation: 'assign_role',
  });

  const safeNote = sanitizeGovernanceNote(note);
  const safeExpiresAt = normalizeExpiresAt(expiresAt);

  await db.query(
    `UPDATE user_roles
     SET is_active = FALSE,
         revoked_at = CURRENT_TIMESTAMP,
         note = COALESCE($3, note)
     WHERE user_id = $1
       AND role_id = $2
       AND is_active = TRUE
       AND revoked_at IS NULL`,
    [targetUserId, role.id, safeNote]
  );

  await db.query(
    `INSERT INTO user_roles (user_id, role_id, assigned_by, note, is_active, expires_at)
     VALUES ($1, $2, $3, $4, TRUE, $5)`,
    [targetUserId, role.id, actorId, safeNote, safeExpiresAt]
  );

  clearAccessProfileCache(targetUserId);

  return getUserAccessProfile(targetUserId);
};

export const revokeRoleFromUser = async (
  actorId: string,
  targetUserId: string,
  roleKey: RoleKey,
  note?: string
) => {
  const roleRes = await db.query('SELECT id, priority FROM roles WHERE role_key = $1 LIMIT 1', [roleKey]);
  const role = roleRes.rows[0] as { id: string; priority: number } | undefined;
  if (!role) {
    throw new Error(`Role not found: ${roleKey}`);
  }

  const actorProfile = await getUserAccessProfile(actorId);
  const targetProfile = await getUserAccessProfile(targetUserId);

  if (!actorProfile || !targetProfile) {
    throw new Error('Actor or target not found');
  }

  assertRoleMutationAllowed({
    actor: actorProfile,
    target: targetProfile,
    targetRoleKey: roleKey,
    mutation: 'revoke_role',
  });

  const safeNote = sanitizeGovernanceNote(note);

  await db.query(
    `UPDATE user_roles
     SET is_active = FALSE,
         revoked_at = CURRENT_TIMESTAMP,
         note = COALESCE($3, note)
     WHERE user_id = $1
       AND role_id = $2
       AND is_active = TRUE
       AND revoked_at IS NULL`,
    [targetUserId, role.id, safeNote]
  );

  clearAccessProfileCache(targetUserId);

  return getUserAccessProfile(targetUserId);
};

export const setUserBlockedFlag = async (
  actorId: string,
  targetUserId: string,
  blocked: boolean,
  label?: string
) => {
  const actorProfile = await getUserAccessProfile(actorId);
  const targetProfile = await getUserAccessProfile(targetUserId);

  if (!actorProfile || !targetProfile) {
    throw new Error('Actor or target not found');
  }

  assertBlockMutationAllowed({
    actor: actorProfile,
    target: targetProfile,
  });

  const safeNote = sanitizeGovernanceNote(label);

  await db.query(
    `UPDATE users
     SET is_system_blocked = $1,
         access_labels = CASE
           WHEN $2::text IS NULL THEN access_labels
           ELSE access_labels || jsonb_build_object('last_block_note', $2::text)
         END,
         updated_at = CURRENT_TIMESTAMP
     WHERE id = $3`,
    [blocked, safeNote, targetUserId]
  );

  clearAccessProfileCache(targetUserId);

  return getUserAccessProfile(targetUserId);
};
