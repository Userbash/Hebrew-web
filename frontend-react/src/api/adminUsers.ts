import api from './client';

export interface AdminUser {
  id: string;
  email: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  role: string;
  xp_total: number;
  level: number;
  registered_at: string | null;
  last_login: string | null;
  failed_login_attempts: number;
  locked_until: string | null;
  is_system_blocked?: boolean;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
  rbac_roles?: string[];
  permission_count?: number;
  publication_count?: number;
  published_publication_count?: number;
}

export interface UserSession {
  id: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string;
  last_seen_at: string | null;
  expires_at: string;
  revoked_at: string | null;
}

export interface UsersListResponse {
  success: boolean;
  users: AdminUser[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface AdminUsersListParams {
  page?: number;
  limit?: number;
  id?: string;
  search?: string;
  role?: string;
  rbacRole?: string;
  permission?: string;
  publicationStatus?: string;
  publicationSearch?: string;
  hasPublications?: boolean;
  includeDeleted?: boolean;
  isBlocked?: boolean;
  sortBy?:
    | 'id'
    | 'username'
    | 'email'
    | 'created_at'
    | 'updated_at'
    | 'registered_at'
    | 'last_login'
    | 'xp_total'
    | 'level'
    | 'publication_count';
  sortOrder?: 'asc' | 'desc';
}

export interface CreateAdminUserPayload {
  email: string;
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export const adminUsersApi = {
  list: async (params: AdminUsersListParams) => {
    const { data } = await api.get<UsersListResponse>('/admin/users', { params });
    return data;
  },

  create: async (payload: CreateAdminUserPayload) => {
    const { data } = await api.post('/admin/users', payload);
    return data as { success: boolean; message: string; user: AdminUser };
  },

  update: async (userId: string, payload: Partial<AdminUser>) => {
    const { data } = await api.patch(`/admin/users/${userId}`, payload);
    return data as { success: boolean; message: string; user: AdminUser };
  },

  softDelete: async (userId: string) => {
    const { data } = await api.delete(`/admin/users/${userId}`);
    return data as { success: boolean; message: string; userId: string };
  },

  restore: async (userId: string) => {
    const { data } = await api.patch(`/admin/users/${userId}/restore`);
    return data as { success: boolean; message: string; user: AdminUser };
  },

  sessions: async (userId: string) => {
    const { data } = await api.get(`/admin/users/${userId}/sessions`);
    return data as { success: boolean; sessions: UserSession[]; count: number };
  },
};
