import type { User } from '../context/AuthContext';
import { hasPermission } from './rbac';

interface TargetUserLike {
  id: string;
  role?: string | null;
  rbac_roles?: string[] | null;
}

const isSuperadminLike = (targetUser: TargetUserLike) => {
  const role = String(targetUser.role || '').toLowerCase();
  const roles = (targetUser.rbac_roles || []).map((item) => String(item).toLowerCase());
  return role === 'superadmin' || roles.includes('root') || roles.includes('platform_admin');
};

const isCurrentSuperadminLike = (currentUser: User) => {
  const legacy = String(currentUser.role || '').toLowerCase();
  const roles = (currentUser.access?.roleKeys || []).map((item) => String(item).toLowerCase());
  return legacy === 'superadmin' || roles.includes('root');
};

export function canEditUserPermissions(currentUser: User | null | undefined, targetUser: TargetUserLike | null | undefined): boolean {
  if (!currentUser || !targetUser) return false;

  if (!hasPermission(currentUser, 'users.permissions.manage')) {
    return false;
  }

  if (currentUser.id === targetUser.id) {
    return false;
  }

  if (isSuperadminLike(targetUser) && !isCurrentSuperadminLike(currentUser)) {
    return false;
  }

  return true;
}
