import api from './client';

export interface AuditEventItem {
  id: number;
  event_key: string;
  actor_user_id: string | null;
  username: string | null;
  email: string | null;
  session_id: string | null;
  area: string;
  resource: string;
  action: string;
  outcome: 'success' | 'error' | 'blocked';
  method: string;
  path: string;
  target_type: string | null;
  target_id: string | null;
  status_code: number;
  ip_address: string | null;
  user_agent: string | null;
  duration_ms: number;
  message: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditMapItem {
  area: string;
  resource: string;
  action: string;
  total: number;
  non_success: number;
}

export interface AdminAuditResponse {
  success: boolean;
  events: AuditEventItem[];
  summary: {
    total: number;
    success: number;
    errors: number;
    blocked: number;
    admin_actions: number;
    site_actions: number;
    avg_duration_ms: number;
  };
  map: AuditMapItem[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface AdminAuditListParams {
  page?: number;
  limit?: number;
  method?: string;
  area?: string;
  resource?: string;
  action?: string;
  outcome?: string;
  path?: string;
  actorId?: string;
  targetId?: string;
  statusCode?: number;
  dateFrom?: string;
  dateTo?: string;
}

export const adminAuditApi = {
  list: async (params: AdminAuditListParams) => {
    const { data } = await api.get<AdminAuditResponse>('/admin/audit/events', { params });
    return data;
  },
};
