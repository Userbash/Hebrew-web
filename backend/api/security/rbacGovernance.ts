import { ROLE_PRIORITY, type RoleKey } from './rbacCatalog.js';

export interface GovernanceAccessProfile {
  userId: string;
  roleKeys: RoleKey[];
  highestRole: RoleKey;
  highestPriority: number;
}

export type GovernanceMutation = 'assign_role' | 'revoke_role' | 'set_block_state';

const RBAC_ADMIN_ROLES: ReadonlySet<RoleKey> = new Set(['root', 'platform_admin']);
const ROOT_ONLY_ROLES: ReadonlySet<RoleKey> = new Set(['root', 'platform_admin']);

const hasAnyRole = (profile: GovernanceAccessProfile, roles: ReadonlySet<RoleKey>) => {
  return profile.roleKeys.some((role) => roles.has(role));
};

export const hasRbacAdminAccess = (profile: GovernanceAccessProfile) => {
  return hasAnyRole(profile, RBAC_ADMIN_ROLES);
};

const assertRoleMutationAllowedForActor = (
  actor: GovernanceAccessProfile,
  targetRoleKey: RoleKey,
  targetRolePriority: number,
  mutation: GovernanceMutation
) => {
  if (!hasRbacAdminAccess(actor)) {
    throw new Error('Only administrators can modify role assignments');
  }

  if (ROOT_ONLY_ROLES.has(targetRoleKey) && actor.highestRole !== 'root') {
    throw new Error('Only root can change root/platform administrator assignments');
  }

  if (actor.highestRole !== 'root' && targetRolePriority >= actor.highestPriority) {
    throw new Error('Cannot modify roles with equal or higher priority than your own');
  }

  if (!Number.isFinite(targetRolePriority)) {
    throw new Error(`Unknown role priority for ${targetRoleKey}`);
  }

  if (!['assign_role', 'revoke_role', 'set_block_state'].includes(mutation)) {
    throw new Error('Unknown governance mutation');
  }
};

export const assertRoleMutationAllowed = (params: {
  actor: GovernanceAccessProfile;
  target: GovernanceAccessProfile;
  targetRoleKey: RoleKey;
  targetRolePriority?: number;
  mutation: GovernanceMutation;
}) => {
  const { actor, target, targetRoleKey, mutation } = params;
  const targetRolePriority = params.targetRolePriority ?? ROLE_PRIORITY[targetRoleKey] ?? Number.NaN;

  if (actor.userId === target.userId) {
    throw new Error('Self role mutation is not allowed');
  }

  assertRoleMutationAllowedForActor(actor, targetRoleKey, targetRolePriority, mutation);

  if (target.highestRole === 'root' && actor.highestRole !== 'root') {
    throw new Error('Only root can modify root user assignments');
  }

  if (target.highestRole === 'platform_admin' && actor.highestRole !== 'root') {
    throw new Error('Only root can modify platform administrator accounts');
  }

  if (actor.highestRole !== 'root' && actor.highestPriority <= target.highestPriority) {
    throw new Error('Cannot modify user with equal or higher privilege level');
  }
};

export const assertBlockMutationAllowed = (params: {
  actor: GovernanceAccessProfile;
  target: GovernanceAccessProfile;
}) => {
  const { actor, target } = params;

  if (!hasRbacAdminAccess(actor)) {
    throw new Error('Only administrators can change user block state');
  }

  if (actor.userId === target.userId) {
    throw new Error('Self block mutation is not allowed');
  }

  if (target.highestRole === 'root' && actor.highestRole !== 'root') {
    throw new Error('Only root can change root user block state');
  }

  if (target.highestRole === 'platform_admin' && actor.highestRole !== 'root') {
    throw new Error('Only root can change platform administrator block state');
  }

  if (actor.highestRole !== 'root' && actor.highestPriority <= target.highestPriority) {
    throw new Error('Cannot change block state for equal or higher privileged user');
  }
};

export const sanitizeGovernanceNote = (value?: string | null) => {
  if (!value) {
    return null;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  if (trimmed.length > 500) {
    throw new Error('Governance note is too long (maximum 500 characters)');
  }

  return trimmed;
};
