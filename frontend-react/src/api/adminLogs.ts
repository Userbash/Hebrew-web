import api from './client';

export interface AdminLogItem {
  id: number;
  user_id: string | null;
  username: string | null;
  email: string | null;
  session_id?: string | null;
  method: string;
  path: string;
  area?: string;
  resource?: string;
  action?: string;
  outcome?: 'success' | 'error' | 'blocked';
  status_code: number;
  ip_address: string | null;
  user_agent: string | null;
  response_time_ms: number;
  target_user_id?: string | null;
  is_authenticated?: boolean;
  login_identifier?: string | null;
  user_role?: string | null;
  highest_role?: string | null;
  role_keys?: string[];
  is_system_blocked?: boolean | null;
  had_previous_login?: boolean | null;
  account_locked?: boolean | null;
  failed_login_attempts?: number | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface AdminLogsResponse {
  success: boolean;
  logs: AdminLogItem[];
  summary: {
    total: number;
    server_errors: number;
    client_errors: number;
    avg_response_ms: number;
    success?: number;
    blocked?: number;
    errors?: number;
    authenticated?: number;
    locked_accounts?: number;
  };
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface AdminLogsListParams {
  page?: number;
  limit?: number;
  method?: string;
  path?: string;
  userId?: string;
  targetUserId?: string;
  statusCode?: number;
  area?: string;
  action?: string;
  outcome?: string;
  userRole?: string;
  loginIdentifier?: string;
  isAuthenticated?: boolean;
  isSystemBlocked?: boolean;
  accountLocked?: boolean;
  hadPreviousLogin?: boolean;
}

export const adminLogsApi = {
  list: async (params: AdminLogsListParams) => {
    const { data } = await api.get<AdminLogsResponse>('/admin/logs', { params });
    return data;
  },
};
