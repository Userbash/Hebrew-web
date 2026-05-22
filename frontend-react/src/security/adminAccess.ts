import type { RoleKey, User } from '../context/AuthContext';

export const ADMIN_ROLES: RoleKey[] = ['root', 'platform_admin'];

export const isAdminUser = (user: User | null | undefined) => {
  if (!user?.access?.roleKeys || user.access.isSystemBlocked) {
    return false;
  }

  return ADMIN_ROLES.some((role) => user.access?.roleKeys.includes(role));
};

export const getDefaultRouteForUser = (user: User | null | undefined) => {
  if (!user) {
    return '/';
  }

  return isAdminUser(user) ? '/admin' : '/cabinet';
};
