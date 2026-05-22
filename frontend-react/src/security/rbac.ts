import type { RoleKey, User } from '../context/AuthContext';

export type PermissionAction = 'create' | 'read' | 'update' | 'delete';
export type PermissionScope = 'own' | 'any';

export interface PermissionCheck {
  resource: string;
  action: PermissionAction;
  scope?: PermissionScope;
}

const ROLE_PRIORITY: Record<string, number> = {
  root: 1000,
  platform_admin: 900,
  security_admin: 800,
  content_admin: 700,
  editor: 600,
  moderator: 500,
  support: 400,
  analyst: 300,
  user: 100,
  admin: 900,
  superadmin: 1000,
};

const ROLE_PERMISSION_KEYS: Record<string, string[]> = {
  root: [
    'users.read',
    'users.update',
    'users.permissions.read',
    'users.permissions.manage',
    'roles.read',
    'roles.assign',
  ],
  platform_admin: [
    'users.read',
    'users.update',
    'users.permissions.read',
    'users.permissions.manage',
    'roles.read',
    'roles.assign',
  ],
  admin: [
    'users.read',
    'users.update',
    'users.permissions.read',
    'users.permissions.manage',
    'roles.read',
    'roles.assign',
  ],
  security_admin: [
    'users.read',
    'users.update',
    'users.permissions.read',
    'roles.read',
  ],
  content_admin: ['users.read'],
  moderator: ['users.read'],
  editor: [],
  analyst: ['users.read'],
  support: ['users.read', 'users.update'],
  user: [],
  superadmin: [
    'users.read',
    'users.update',
    'users.permissions.read',
    'users.permissions.manage',
    'roles.read',
    'roles.assign',
  ],
};

const ROLE_PERMISSIONS: Record<string, Array<{ resource: string; action: PermissionAction; scope: PermissionScope }>> = {
  root: [
    { resource: '*', action: 'create', scope: 'any' },
    { resource: '*', action: 'read', scope: 'any' },
    { resource: '*', action: 'update', scope: 'any' },
    { resource: '*', action: 'delete', scope: 'any' },
  ],
  platform_admin: [
    { resource: '*', action: 'read', scope: 'any' },
    { resource: '*', action: 'create', scope: 'any' },
    { resource: '*', action: 'update', scope: 'any' },
    { resource: '*', action: 'delete', scope: 'any' },
  ],
  security_admin: [
    { resource: 'system', action: 'read', scope: 'any' },
    { resource: 'rbac', action: 'read', scope: 'any' },
    { resource: 'users', action: 'read', scope: 'any' },
    { resource: 'users', action: 'update', scope: 'any' },
    { resource: 'telemetry', action: 'read', scope: 'any' },
    { resource: 'telemetry', action: 'delete', scope: 'any' },
  ],
  content_admin: [
    { resource: 'publications', action: 'create', scope: 'any' },
    { resource: 'publications', action: 'read', scope: 'any' },
    { resource: 'publications', action: 'update', scope: 'any' },
    { resource: 'publications', action: 'delete', scope: 'any' },
  ],
  moderator: [
    { resource: 'publications', action: 'read', scope: 'any' },
    { resource: 'publications', action: 'update', scope: 'any' },
    { resource: 'users', action: 'read', scope: 'any' },
  ],
  editor: [
    { resource: 'publications', action: 'create', scope: 'own' },
    { resource: 'publications', action: 'read', scope: 'own' },
    { resource: 'publications', action: 'update', scope: 'own' },
    { resource: 'publications', action: 'delete', scope: 'own' },
  ],
  analyst: [
    { resource: 'system', action: 'read', scope: 'any' },
    { resource: 'telemetry', action: 'read', scope: 'any' },
  ],
  user: [
    { resource: 'progress', action: 'read', scope: 'own' },
    { resource: 'users', action: 'read', scope: 'own' },
    { resource: 'users', action: 'update', scope: 'own' },
  ],
};

export const getHighestRole = (roles: RoleKey[] = []) => {
  const sorted = [...roles].sort((a, b) => (ROLE_PRIORITY[b] || 0) - (ROLE_PRIORITY[a] || 0));
  return sorted[0] || 'user';
};

const userRoleSet = (user: User | null | undefined) => {
  const keys = user?.access?.roleKeys || [];
  const role = user?.role ? [String(user.role).toLowerCase()] : [];
  return new Set<string>([...keys.map((r) => String(r).toLowerCase()), ...role]);
};

export const hasPermission = (user: User | null | undefined, check: PermissionCheck | string) => {
  if (!user || user.access?.isSystemBlocked) {
    return false;
  }

  const roles = userRoleSet(user);

  if (typeof check === 'string') {
    return Array.from(roles).some((role) => (ROLE_PERMISSION_KEYS[role] || []).includes(check));
  }

  return Array.from(roles).some((role) => {
    const rules = ROLE_PERMISSIONS[role] || [];
    return rules.some((rule) => {
      const resourceMatches = rule.resource === '*' || rule.resource === check.resource;
      const actionMatches = rule.action === check.action;
      const scopeMatches = !check.scope || check.scope === rule.scope || rule.scope === 'any';
      return resourceMatches && actionMatches && scopeMatches;
    });
  });
};

export const canReadPublicContent = () => true;

export const canAccessCabinet = (user: User | null | undefined) => Boolean(user && !user.access?.isSystemBlocked);

export const canModerateContent = (user: User | null | undefined) => {
  return hasPermission(user, { resource: 'publications', action: 'update', scope: 'any' });
};
