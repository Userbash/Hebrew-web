import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { usePreferencesStore, type UserPreferencesPayload } from '../store/preferencesStore';

type PreferencesResponse = {
  success: boolean;
  preferences?: UserPreferencesPayload;
};

export default function PreferencesSync() {
  const { user, setUser } = useAuth();
  const applyRemotePreferences = usePreferencesStore((state) => state.applyRemotePreferences);

  const preferencesQuery = useQuery<UserPreferencesPayload>({
    queryKey: ['preferences', user?.id],
    enabled: Boolean(user?.id),
    queryFn: async () => {
      const response = await api.get<PreferencesResponse>('/users/preferences');
      return response.data.preferences || {};
    },
    staleTime: 60_000,
  });

  useEffect(() => {
    if (!preferencesQuery.data) return;
    applyRemotePreferences(preferencesQuery.data);
    setUser((prev) => (prev ? { ...prev, ui_preferences: { ...(prev.ui_preferences || {}), ...preferencesQuery.data } } : prev));
  }, [preferencesQuery.data, applyRemotePreferences, setUser]);

  return null;
}
