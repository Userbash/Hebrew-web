import React, { createContext, useContext, useEffect, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { usePreferencesStore, type Theme, type ThemeMode } from '../store/preferencesStore';

export type { Theme, ThemeMode };

interface ThemeContextType {
  theme: Theme;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const themeMode = usePreferencesStore((state) => state.themeMode);
  const systemTheme = usePreferencesStore((state) => state.systemTheme);
  const hydrateLocal = usePreferencesStore((state) => state.hydrateLocal);
  const setThemeMode = usePreferencesStore((state) => state.setThemeMode);
  const setSystemTheme = usePreferencesStore((state) => state.setSystemTheme);
  const applyRemotePreferences = usePreferencesStore((state) => state.applyRemotePreferences);

  useEffect(() => {
    hydrateLocal();
  }, [hydrateLocal]);

  useEffect(() => {
    if (!user?.id) return;
    applyRemotePreferences(user.ui_preferences || {});
  }, [user?.id, user?.ui_preferences, applyRemotePreferences]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const listener = () => setSystemTheme(media.matches ? 'dark' : 'light');
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [setSystemTheme]);

  const theme = useMemo<Theme>(() => (themeMode === 'system' ? systemTheme : themeMode), [themeMode, systemTheme]);

  const toggleTheme = () => {
    if (themeMode === 'system') {
      setThemeMode(systemTheme === 'dark' ? 'light' : 'dark');
      return;
    }
    setThemeMode(themeMode === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, themeMode, setThemeMode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
