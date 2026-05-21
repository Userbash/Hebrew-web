import React, { createContext, useContext, useState } from 'react';

type Language = 'ru' | 'en' | 'he';

interface Translations {
  welcome: string;
  username: string;
  password: string;
  login: string;
  cancel: string;
  rememberMe: string;
  forgotPassword: string;
  settings: string;
}

const translations: Record<Language, Translations> = {
  ru: {
    welcome: 'Добро пожаловать!',
    username: 'Имя пользователя или Email',
    password: 'Пароль',
    login: 'Войти',
    cancel: 'Отмена',
    rememberMe: 'Запомнить меня',
    forgotPassword: 'Забыли пароль?',
    settings: 'Настройки',
  },
  en: {
    welcome: 'Welcome Back!',
    username: 'Username or Email',
    password: 'Password',
    login: 'Authorize',
    cancel: 'Cancel',
    rememberMe: 'Remember Me',
    forgotPassword: 'Forgot password?',
    settings: 'Settings',
  },
  he: {
    welcome: 'ברוך הבא!',
    username: 'שם משתמש או אימייל',
    password: 'סיסמה',
    login: 'התחברות',
    cancel: 'ביטול',
    rememberMe: 'זכור אותי',
    forgotPassword: 'שכחת סיסמה?',
    settings: 'הגדרות',
  },
};

interface LanguageContextType {
  language: Language;
  t: Translations;
  setLanguage: (lang: Language) => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>(() => {
    const browserLang = navigator.language.split('-')[0];
    if (browserLang === 'he') return 'he';
    if (browserLang === 'ru') return 'ru';
    return 'en';
  });

  const t = translations[language];

  return (
    <LanguageContext.Provider value={{ language, t, setLanguage }}>
      <div dir={language === 'he' ? 'rtl' : 'ltr'}>
        {children}
      </div>
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
