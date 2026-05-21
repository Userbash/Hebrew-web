import api from './client';
import type { RoleKey, AccessProfile } from '../context/AuthContext';

export interface CatalogRole {
  id: string;
  management_key: string;
  role_key: RoleKey;
  title: string;
  description: string | null;
  priority: number;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface CatalogPermission {
  id: string;
  permission_key: string;
  permission_name: string;
  resource: string;
  action: 'create' | 'read' | 'update' | 'delete';
  scope: 'own' | 'any';
  description: string | null;
  created_at: string;
}

export interface UserRoleAssignment {
  id: string;
  assignment_key: string;
  role_key: RoleKey;
  title: string;
  priority: number;
  note: string | null;
  is_active: boolean;
  assigned_at: string;
  expires_at: string | null;
  revoked_at: string | null;
  assigned_by: string | null;
}

export const accessApi = {
  getCatalog: async () => {
    const { data } = await api.get('/admin/access/catalog');
    return data as {
      success: boolean;
      hierarchy: Array<{
        role: RoleKey;
        title: string;
        priority: number;
        summary: string;
        privileges: string[];
      }>;
      roles: CatalogRole[];
      permissions: CatalogPermission[];
      rolePermissions: Array<{
        role_key: RoleKey;
        permission_name: string;
        resource: string;
        action: string;
        scope: string;
        granted: boolean;
        policy_key: string;
        note: string | null;
      }>;
    };
  },

  getUserAccess: async (userId: string) => {
    const { data } = await api.get(`/admin/access/users/${userId}`);
    return data as {
      success: boolean;
      profile: AccessProfile;
      assignments: UserRoleAssignment[];
    };
  },

  assignRole: async (userId: string, roleKey: RoleKey, note?: string, expiresAt?: string | null) => {
    const { data } = await api.post(`/admin/access/users/${userId}/roles`, {
      roleKey,
      note,
      expiresAt: expiresAt ?? null,
    });

    return data as {
      success: boolean;
      message: string;
      profile: AccessProfile | null;
    };
  },

  revokeRole: async (userId: string, roleKey: RoleKey, note?: string) => {
    const { data } = await api.delete(`/admin/access/users/${userId}/roles/${roleKey}`, {
      data: { note },
    });

    return data as {
      success: boolean;
      message: string;
      profile: AccessProfile | null;
    };
  },

  setBlockedState: async (userId: string, blocked: boolean, note?: string) => {
    const { data } = await api.patch(`/admin/access/users/${userId}/block`, {
      blocked,
      note,
    });

    return data as {
      success: boolean;
      message: string;
      profile: AccessProfile | null;
    };
  },
};
