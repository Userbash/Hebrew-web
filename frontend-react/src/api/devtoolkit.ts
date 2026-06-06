import api from './client';

export type DevToolkitMode = 'plan' | 'dry_run' | 'apply' | 'review' | 'repo';

export interface DevToolkitRequest {
  session_id: string;
  message: string;
  mode: DevToolkitMode;
  repo_context: boolean;
  allow_code_changes: boolean;
  allow_execution: boolean;
  dry_run: boolean;
}

export interface DevToolkitSession {
  session_id: string;
  title: string;
  mode: DevToolkitMode | string;
  repo_context: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_summary: string;
}

export interface DevToolkitMessage {
  message_id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system' | string;
  content: string;
  created_at: string;
  meta: Record<string, unknown>;
}

export interface DevToolkitResponse {
  session_id: string;
  summary: string;
  plan: Record<string, unknown>;
  tasks: Array<Record<string, unknown>>;
  agents: Array<Record<string, unknown>>;
  diff: string | null;
  clipboard_payload: string | null;
  fulltrace: Record<string, unknown>;
  status: string;
}

export interface DevToolkitClipboardItem {
  session_id: string;
  item_type: string;
  content: string;
  label?: string | null;
}

export const devToolkitApi = {
  async createSession(payload: Partial<Pick<DevToolkitSession, 'session_id' | 'mode' | 'repo_context'>>) {
    const response = await api.post('/devtoolkit/sessions', payload);
    return response.data as { status: string; session: DevToolkitSession };
  },

  async listSessions() {
    const response = await api.get('/devtoolkit/sessions');
    return response.data as { status: string; sessions: DevToolkitSession[] };
  },

  async getSessionMessages(sessionId: string) {
    const response = await api.get(`/devtoolkit/sessions/${encodeURIComponent(sessionId)}/messages`);
    return response.data as { status: string; session_id: string; messages: DevToolkitMessage[] };
  },

  async getSessionDiff(sessionId: string) {
    const response = await api.get(`/devtoolkit/sessions/${encodeURIComponent(sessionId)}/diff`);
    return response.data as { session_id: string; diff: string | null; status: string };
  },

  async chat(payload: DevToolkitRequest) {
    const response = await api.post('/devtoolkit/chat', payload);
    return response.data as DevToolkitResponse;
  },

  async execute(payload: DevToolkitRequest) {
    const response = await api.post('/devtoolkit/execute', payload);
    return response.data as Record<string, unknown>;
  },

  async saveClipboard(payload: DevToolkitClipboardItem) {
    const response = await api.post('/devtoolkit/clipboard', payload);
    return response.data as { status: string; item: Record<string, unknown> };
  },
};

export default devToolkitApi;
