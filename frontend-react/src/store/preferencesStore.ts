import { create } from 'zustand';

export type Theme = 'light' | 'dark';
export type ThemeMode = Theme | 'system';
export type Language = 'ru' | 'en' | 'he';
export type LanguageMode = Language | 'system';

export interface UserPreferencesPayload {
  themeMode?: ThemeMode;
  language?: Language;
  languageMode?: LanguageMode;
}

const THEME_STORAGE_KEY = 'ui_theme_mode';
const LANGUAGE_STORAGE_KEY = 'ui_language';
const LANGUAGE_MODE_STORAGE_KEY = 'ui_language_mode';

const detectSystemTheme = (): Theme => {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const normalizeLanguage = (value?: string | null): Language | null => {
  if (!value) return null;
  const trimmed = value.toLowerCase().trim();
  if (trimmed === 'ru' || trimmed.startsWith('ru-')) return 'ru';
  if (trimmed === 'he' || trimmed.startsWith('he-') || trimmed === 'iw' || trimmed.startsWith('iw-')) return 'he';
  if (trimmed === 'en' || trimmed.startsWith('en-')) return 'en';
  return null;
};

const detectSystemLanguage = (): Language => {
  if (typeof window === 'undefined') return 'en';
  return normalizeLanguage(window.navigator.language) || 'en';
};

const readThemeMode = (): ThemeMode => {
  if (typeof window === 'undefined') return 'system';
  const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (saved === 'light' || saved === 'dark' || saved === 'system') return saved;
  return 'system';
};

const readLanguageMode = (): LanguageMode => {
  if (typeof window === 'undefined') return 'system';
  const saved = window.localStorage.getItem(LANGUAGE_MODE_STORAGE_KEY);
  if (saved === 'ru' || saved === 'en' || saved === 'he' || saved === 'system') return saved;
  return 'system';
};

const readLanguage = (): Language => {
  if (typeof window === 'undefined') return 'en';
  const saved = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (saved === 'ru' || saved === 'en' || saved === 'he') return saved;
  return detectSystemLanguage();
};

const applyTheme = (mode: ThemeMode, systemTheme: Theme) => {
  if (typeof document === 'undefined') return;
  const resolved = mode === 'system' ? systemTheme : mode;
  const root = document.documentElement;
  root.dataset.theme = resolved;
  root.classList.remove('light', 'dark');
  root.classList.add(resolved);
};

type PreferencesState = {
  themeMode: ThemeMode;
  systemTheme: Theme;
  languageMode: LanguageMode;
  language: Language;
  hydrateLocal: () => void;
  setSystemTheme: (theme: Theme) => void;
  setThemeMode: (mode: ThemeMode) => void;
  setLanguage: (language: Language) => void;
  setLanguageMode: (mode: LanguageMode) => void;
  applyRemotePreferences: (prefs: UserPreferencesPayload) => void;
};

export const usePreferencesStore = create<PreferencesState>((set, get) => ({
  themeMode: 'system',
  systemTheme: detectSystemTheme(),
  languageMode: 'system',
  language: detectSystemLanguage(),

  hydrateLocal: () => {
    const themeMode = readThemeMode();
    const languageMode = readLanguageMode();
    const language = languageMode === 'system' ? readLanguage() : languageMode;
    set({ themeMode, languageMode, language });
    applyTheme(themeMode, get().systemTheme);
  },

  setSystemTheme: (theme) => {
    set({ systemTheme: theme });
    applyTheme(get().themeMode, theme);
  },

  setThemeMode: (mode) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(THEME_STORAGE_KEY, mode);
    }
    set({ themeMode: mode });
    applyTheme(mode, get().systemTheme);
  },

  setLanguage: (language) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
      window.localStorage.setItem(LANGUAGE_MODE_STORAGE_KEY, language);
    }
    set({ language, languageMode: language });
  },

  setLanguageMode: (mode) => {
    const nextLanguage = mode === 'system' ? detectSystemLanguage() : mode;
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(LANGUAGE_MODE_STORAGE_KEY, mode);
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, nextLanguage);
    }
    set({ languageMode: mode, language: nextLanguage });
  },

  applyRemotePreferences: (prefs) => {
    const nextThemeMode = prefs.themeMode;
    const nextLanguageMode = prefs.languageMode;
    const nextLanguage = prefs.language;

    if (nextThemeMode === 'light' || nextThemeMode === 'dark' || nextThemeMode === 'system') {
      get().setThemeMode(nextThemeMode);
    }

    if (nextLanguageMode === 'ru' || nextLanguageMode === 'en' || nextLanguageMode === 'he' || nextLanguageMode === 'system') {
      get().setLanguageMode(nextLanguageMode);
    } else if (nextLanguage === 'ru' || nextLanguage === 'en' || nextLanguage === 'he') {
      get().setLanguage(nextLanguage);
    }
  },
}));

