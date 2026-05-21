import api from './client';

export interface Publication {
  id: string;
  name: string;
  description: string | null;
  category: string;
  metadata: {
    authorId?: string;
    status?: string;
    tags?: string[];
    visibility?: 'private' | 'team' | 'public';
    publishedAt?: string | null;
    [key: string]: unknown;
  } | null;
  created_at: string;
  updated_at: string;
}

export const publicationsApi = {
  list: async (params?: { search?: string; status?: string; authorId?: string }) => {
    const { data } = await api.get('/admin/publications', { params });
    return data as { success: boolean; publications: Publication[]; count: number };
  },

  create: async (payload: {
    title: string;
    description?: string;
    status?: string;
    visibility?: 'private' | 'team' | 'public';
    tags?: string[];
  }) => {
    const { data } = await api.post('/admin/publications', payload);
    return data as { success: boolean; message: string; publication: Publication };
  },

  update: async (id: string, payload: Partial<{
    title: string;
    description: string;
    status: string;
    metadata: Record<string, unknown>;
  }>) => {
    const { data } = await api.put(`/admin/publications/${id}`, payload);
    return data as { success: boolean; message: string; publication: Publication };
  },

  remove: async (id: string) => {
    const { data } = await api.delete(`/admin/publications/${id}`);
    return data as { success: boolean; message: string; id: string };
  },
};
