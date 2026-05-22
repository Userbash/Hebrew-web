import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useAuth } from './AuthContext';

export type Theme = 'light' | 'dark';
export type ThemeMode = Theme | 'system';

interface ThemeContextType {
  theme: Theme;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);
const THEME_STORAGE_KEY = 'ui_theme_mode';

const resolveSystemTheme = (): Theme => {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const readThemeMode = (userId?: string | null): ThemeMode => {
  if (typeof window === 'undefined') return 'system';

  const userScopedKey = userId ? `${THEME_STORAGE_KEY}:${userId}` : null;
  const saved = (userScopedKey ? window.localStorage.getItem(userScopedKey) : null)
    || window.localStorage.getItem(THEME_STORAGE_KEY);

  if (saved === 'light' || saved === 'dark' || saved === 'system') return saved;
  return 'system';
};

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => readThemeMode(null));
  const [systemTheme, setSystemTheme] = useState<Theme>(resolveSystemTheme);

  useEffect(() => {
    const remoteTheme = user?.ui_preferences?.themeMode;
    if (remoteTheme === "system" || remoteTheme === "light" || remoteTheme === "dark") {
      setThemeMode(remoteTheme);
      return;
    }
    setThemeMode(readThemeMode(user?.id ?? null));
  }, [user?.id]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const listener = () => setSystemTheme(media.matches ? 'dark' : 'light');
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, []);

  const theme = useMemo<Theme>(() => (themeMode === 'system' ? systemTheme : themeMode), [themeMode, systemTheme]);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);

    if (user?.id) {
      window.localStorage.setItem(`${THEME_STORAGE_KEY}:${user.id}`, themeMode);
    } else {
      window.localStorage.setItem(THEME_STORAGE_KEY, themeMode);
    }
  }, [theme, themeMode, user?.id]);

  const toggleTheme = () => {
    setThemeMode((prev) => {
      if (prev === 'system') return systemTheme === 'dark' ? 'light' : 'dark';
      return prev === 'light' ? 'dark' : 'light';
    });
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
