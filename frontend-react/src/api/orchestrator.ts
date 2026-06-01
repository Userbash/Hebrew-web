import api from './client';

interface OrchestratorChatRequest {
  message: string;
  session_id?: string;
  user_id?: string;
  provider?: 'gpt' | 'gemini' | 'auto';
}

interface OrchestratorChatResponse {
  success: boolean;
  status: 'completed' | 'pending';
  provider: 'gpt' | 'gemini' | 'auto';
  orchestrator_url: string;
  data: unknown;
  error?: string;
  message?: string;
  details?: Record<string, unknown>;
}

interface OrchestratorHealthResponse {
  success: boolean;
  orchestrator_url: string;
  bridge_status: number;
  bridge_response: unknown;
  error?: string;
  message?: string;
}

export const chatWithOrchestrator = async (
  payload: OrchestratorChatRequest
): Promise<OrchestratorChatResponse> => {
  const response = await api.post<OrchestratorChatResponse>('/orchestrator/chat', payload);
  return response.data;
};

export const getOrchestratorChatHealth = async (): Promise<OrchestratorHealthResponse> => {
  const response = await api.get<OrchestratorHealthResponse>('/orchestrator/chat/health');
  return response.data;
};
