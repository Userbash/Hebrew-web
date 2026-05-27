import type { RoleKey, User } from '../context/AuthContext';

export const ADMIN_ROLES: RoleKey[] = ['root', 'platform_admin'];

const LEGACY_ADMIN_ROLES = new Set(['admin', 'superadmin', 'root', 'platform_admin']);

export const isAdminUser = (user: User | null | undefined) => {
  if (!user) {
    return false;
  }

  const roleKeys = user.access?.roleKeys || [];
  const legacyRole = String(user.role || '').trim().toLowerCase();
  const isBlocked = Boolean(user.access?.isSystemBlocked);

  if (isBlocked) {
    return false;
  }

  if (ADMIN_ROLES.some((role) => roleKeys.includes(role))) {
    return true;
  }

  return LEGACY_ADMIN_ROLES.has(legacyRole);
};

export const getDefaultRouteForUser = (user: User | null | undefined) => {
  if (!user) {
    return '/';
  }

  return isAdminUser(user) ? '/admin' : '/cabinet';
};
