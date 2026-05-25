import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Languages, Monitor, Moon, Sun } from 'lucide-react';
import { useLanguage, type Language } from '../../context/LanguageContext';
import { useTheme, type ThemeMode } from '../../context/ThemeContext';
import { useAuth, type UserUiPreferences } from '../../context/AuthContext';
import api from '../../api/client';

interface UiPreferencesControlsProps {
  className?: string;
}

const LANGUAGE_OPTIONS: Array<{ value: Language | 'system'; label: string }> = [
  { value: 'system', label: '__SYSTEM__' },
  { value: 'en', label: 'English' },
  { value: 'ru', label: 'Русский' },
  ];

export default function UiPreferencesControls({ className = '' }: UiPreferencesControlsProps) {
  const { languageMode, setLanguage, setLanguageMode, t } = useLanguage();
  const { themeMode, setThemeMode } = useTheme();
  const { user, setUser } = useAuth();
  const queryClient = useQueryClient();

  const persistMutation = useMutation({
    mutationFn: async (patch: Partial<UserUiPreferences>) => {
      if (!user?.id || Object.keys(patch).length === 0) return null;
      const response = await api.put('/users/preferences', { preferences: patch });
      return response.data?.preferences || patch;
    },
    onSuccess: (preferences) => {
      if (!preferences) return;
      setUser((prev) => (prev ? { ...prev, ui_preferences: { ...(prev.ui_preferences || {}), ...preferences } } : prev));
      queryClient.setQueryData(['preferences', user?.id], preferences);
    },
  });

  const persistPreferences = (patch: Partial<UserUiPreferences>) => {
    if (!user?.id || Object.keys(patch).length === 0) return;
    void persistMutation.mutateAsync(patch);
  };

  return (
    <div className={`ui-prefs ${className}`.trim()} aria-label={t.loginSettingsAria}>
      <label className="ui-prefs-control" aria-label={t.languageAria}>
        <Languages size={16} />
        <select
          value={languageMode}
          onChange={(e) => {
            const next = e.target.value as Language | 'system';
            if (next === 'system') {
              if (languageMode !== 'system') {
                setLanguageMode('system');
                persistPreferences({ languageMode: 'system' });
              }
              return;
            }

            if (languageMode !== next) {
              setLanguage(next);
              persistPreferences({ language: next, languageMode: next });
            }
          }}
        >
          {LANGUAGE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>{option.label === '__SYSTEM__' ? t.languageSystem : option.label}</option>
          ))}
        </select>
      </label>

      <label className="ui-prefs-control" aria-label={t.toggleThemeAria}>
        {themeMode === 'light' ? <Sun size={16} /> : themeMode === 'dark' ? <Moon size={16} /> : <Monitor size={16} />}
        <select
          value={themeMode}
          onChange={(e) => {
            const next = e.target.value as ThemeMode;
            if (themeMode !== next) {
              setThemeMode(next);
              persistPreferences({ themeMode: next });
            }
          }}
        >
          <option value="system">{t.themeSystem}</option>
          <option value="light">{t.themeLight}</option>
          <option value="dark">{t.themeDark}</option>
        </select>
      </label>
    </div>
  );
}
