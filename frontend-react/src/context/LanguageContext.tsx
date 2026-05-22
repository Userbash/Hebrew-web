import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';

export type Language = 'ru' | 'en' | 'he';

interface Translations {
  welcome: string;
  username: string;
  password: string;
  login: string;
  cancel: string;
  rememberMe: string;
  forgotPassword: string;
  settings: string;

  loginSettingsAria: string;
  languageAria: string;
  languageSystem: string;
  toggleThemeAria: string;
  themeSystem: string;
  themeLight: string;
  themeDark: string;
  loginHeroTitle: string;
  loginHeroDesc: string;
  loginCardKicker: string;
  loginCardTitle: string;
  loginCardDesc: string;
  emailLabel: string;
  passwordLabel: string;
  passwordPlaceholder: string;
  loginSubmitting: string;
  loginErrorDefault: string;
  noAccount: string;
  createAccess: string;

  registerHeroTitle: string;
  registerHeroDesc: string;
  registerCardTitle: string;
  usernameLabel: string;
  usernamePlaceholder: string;
  registerPasswordPlaceholder: string;
  passwordRulesHint: string;
  confirmPasswordLabel: string;
  confirmPasswordPlaceholder: string;
  acceptTerms: string;
  registerSubmit: string;
  registerSubmitting: string;
  registerErrorDefault: string;
  alreadyHasAccount: string;
  signIn: string;

  dashboardNavAria: string;
  navOverview: string;
  navLessons: string;
  navProgress: string;
  navSettings: string;
  logout: string;
  today: string;
  hello: string;
  dashboardSubtitle: string;
  searchPlaceholder: string;
  systemOnline: string;
  dayReadyTitle: string;
  dayReadyDesc: string;
  continueLesson: string;
  statsAria: string;
  activeLessons: string;
  weeklyProgress: string;
  security: string;
  newItems: string;
  zeroIncidents: string;
  recentActions: string;
  all: string;
  activity1Title: string;
  activity2Title: string;
  activity3Title: string;
  twoHoursAgo: string;
  yesterday: string;
  threeDaysAgo: string;
  envStatusTitle: string;
  updatedNow: string;
  stable: string;
  stableDesc: string;
  adminTitle: string;
  adminOperator: string;
  adminReady: string;

  initAccess: string;
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

    loginSettingsAria: 'Настройки входа',
    languageAria: 'Язык интерфейса',
    languageSystem: 'Системный',
    toggleThemeAria: 'Переключить тему',
    themeSystem: 'Системная',
    themeLight: 'Светлая',
    themeDark: 'Темная',
    loginHeroTitle: 'Учите иврит в понятном рабочем кабинете',
    loginHeroDesc: 'Войдите, чтобы продолжить уроки, повторить слова и посмотреть прогресс без лишних панелей и сложных настроек.',
    loginCardKicker: 'Личный кабинет',
    loginCardTitle: 'Вход',
    loginCardDesc: 'Используйте email и пароль аккаунта.',
    emailLabel: 'Email',
    passwordLabel: 'Пароль',
    passwordPlaceholder: 'Введите пароль',
    loginSubmitting: 'Вход...',
    loginErrorDefault: 'Не удалось войти. Проверьте email и пароль.',
    noAccount: 'Нет аккаунта?',
    createAccess: 'Создать доступ',

    registerHeroTitle: 'Учите иврит в понятном рабочем кабинете',
    registerHeroDesc: 'Создайте аккаунт для начала обучения.',
    registerCardTitle: 'Регистрация',
    usernameLabel: 'Username',
    usernamePlaceholder: 'Например: ivan.petrov',
    registerPasswordPlaceholder: 'Введите сложный пароль',
    passwordRulesHint: 'Минимум 12 символов, заглавная/строчная буква, цифра и спецсимвол, без пробелов',
    confirmPasswordLabel: 'Подтверждение пароля',
    confirmPasswordPlaceholder: 'Повторите пароль',
    acceptTerms: 'Согласен с условиями',
    registerSubmit: 'Зарегистрироваться',
    registerSubmitting: 'Регистрация...',
    registerErrorDefault: 'Ошибка регистрации',
    alreadyHasAccount: 'Уже есть аккаунт?',
    signIn: 'Войти',

    dashboardNavAria: 'Главная навигация',
    navOverview: 'Обзор',
    navLessons: 'Уроки',
    navProgress: 'Прогресс',
    navSettings: 'Настройки',
    logout: 'Выйти',
    today: 'Сегодня',
    hello: 'Здравствуйте',
    dashboardSubtitle: 'Продолжайте обучение и следите за состоянием платформы.',
    searchPlaceholder: 'Найти урок, слово или отчёт',
    systemOnline: 'Система работает',
    dayReadyTitle: 'Ваш учебный день готов',
    dayReadyDesc: '3 коротких упражнения и один словарный повтор помогут сохранить темп без перегрузки.',
    continueLesson: 'Продолжить урок',
    statsAria: 'Ключевые показатели',
    activeLessons: 'Активные уроки',
    weeklyProgress: 'Прогресс недели',
    security: 'Безопасность',
    newItems: '2 новых',
    zeroIncidents: '0 событий',
    recentActions: 'Последние действия',
    all: 'Все',
    activity1Title: 'Урок: базовая грамматика',
    activity2Title: 'Повтор: современная лексика',
    activity3Title: 'Тест: технические термины',
    twoHoursAgo: '2 часа назад',
    yesterday: 'Вчера',
    threeDaysAgo: '3 дня назад',
    envStatusTitle: 'Состояние среды',
    updatedNow: 'Обновлено сейчас',
    stable: 'Стабильно',
    stableDesc: 'API, база данных и учебные сервисы отвечают в пределах нормы.',
    adminTitle: 'Центр администрирования',
    adminOperator: 'Оператор системы',
    adminReady: 'Главная административная консоль готова к командам.',

    initAccess: 'Инициализировать доступ',
  },
  en: {
    welcome: 'Welcome Back!',
    username: 'Username or Email',
    password: 'Password',
    login: 'Sign In',
    cancel: 'Cancel',
    rememberMe: 'Remember Me',
    forgotPassword: 'Forgot password?',
    settings: 'Settings',

    loginSettingsAria: 'Login settings',
    languageAria: 'Interface language',
    languageSystem: 'System',
    toggleThemeAria: 'Toggle theme',
    themeSystem: 'System',
    themeLight: 'Light',
    themeDark: 'Dark',
    loginHeroTitle: 'Learn Hebrew in a clear workspace',
    loginHeroDesc: 'Sign in to continue lessons, review words, and track progress without extra complexity.',
    loginCardKicker: 'Personal account',
    loginCardTitle: 'Sign In',
    loginCardDesc: 'Use your account email and password.',
    emailLabel: 'Email',
    passwordLabel: 'Password',
    passwordPlaceholder: 'Enter password',
    loginSubmitting: 'Signing in...',
    loginErrorDefault: 'Could not sign in. Check your email and password.',
    noAccount: 'No account?',
    createAccess: 'Create access',

    registerHeroTitle: 'Learn Hebrew in a clear workspace',
    registerHeroDesc: 'Create an account to start learning.',
    registerCardTitle: 'Sign Up',
    usernameLabel: 'Username',
    usernamePlaceholder: 'For example: john.doe',
    registerPasswordPlaceholder: 'Enter a strong password',
    passwordRulesHint: 'At least 12 chars, upper/lowercase, number, special char, no spaces',
    confirmPasswordLabel: 'Confirm password',
    confirmPasswordPlaceholder: 'Repeat password',
    acceptTerms: 'I agree to the terms',
    registerSubmit: 'Create account',
    registerSubmitting: 'Creating...',
    registerErrorDefault: 'Registration error',
    alreadyHasAccount: 'Already have an account?',
    signIn: 'Sign In',

    dashboardNavAria: 'Main navigation',
    navOverview: 'Overview',
    navLessons: 'Lessons',
    navProgress: 'Progress',
    navSettings: 'Settings',
    logout: 'Log out',
    today: 'Today',
    hello: 'Hello',
    dashboardSubtitle: 'Continue learning and monitor platform status.',
    searchPlaceholder: 'Find lesson, word, or report',
    systemOnline: 'System online',
    dayReadyTitle: 'Your learning day is ready',
    dayReadyDesc: '3 short exercises and one vocabulary review will keep your pace without overload.',
    continueLesson: 'Continue lesson',
    statsAria: 'Key metrics',
    activeLessons: 'Active lessons',
    weeklyProgress: 'Weekly progress',
    security: 'Security',
    newItems: '2 new',
    zeroIncidents: '0 incidents',
    recentActions: 'Recent activity',
    all: 'All',
    activity1Title: 'Lesson: basic grammar',
    activity2Title: 'Review: modern vocabulary',
    activity3Title: 'Test: technical terms',
    twoHoursAgo: '2 hours ago',
    yesterday: 'Yesterday',
    threeDaysAgo: '3 days ago',
    envStatusTitle: 'Environment status',
    updatedNow: 'Updated now',
    stable: 'Stable',
    stableDesc: 'API, database, and learning services respond within normal range.',
    adminTitle: 'Admin control center',
    adminOperator: 'System operator',
    adminReady: 'Main administrative console is ready for commands.',

    initAccess: 'Initialize access',
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

    loginSettingsAria: 'הגדרות התחברות',
    languageAria: 'שפת ממשק',
    languageSystem: 'מערכת',
    toggleThemeAria: 'החלף ערכת נושא',
    themeSystem: 'מערכת',
    themeLight: 'בהיר',
    themeDark: 'כהה',
    loginHeroTitle: 'למד עברית בסביבת עבודה ברורה',
    loginHeroDesc: 'התחבר כדי להמשיך שיעורים, לחזור על מילים ולעקוב אחרי ההתקדמות בלי עומס מיותר.',
    loginCardKicker: 'אזור אישי',
    loginCardTitle: 'התחברות',
    loginCardDesc: 'השתמש באימייל ובסיסמה של החשבון שלך.',
    emailLabel: 'אימייל',
    passwordLabel: 'סיסמה',
    passwordPlaceholder: 'הזן סיסמה',
    loginSubmitting: 'מתחבר...',
    loginErrorDefault: 'ההתחברות נכשלה. בדוק אימייל וסיסמה.',
    noAccount: 'אין לך חשבון?',
    createAccess: 'צור גישה',

    registerHeroTitle: 'למד עברית בסביבת עבודה ברורה',
    registerHeroDesc: 'צור חשבון כדי להתחיל ללמוד.',
    registerCardTitle: 'הרשמה',
    usernameLabel: 'שם משתמש',
    usernamePlaceholder: 'לדוגמה: daniel.levi',
    registerPasswordPlaceholder: 'הזן סיסמה חזקה',
    passwordRulesHint: 'לפחות 12 תווים, אות גדולה/קטנה, מספר, תו מיוחד, ללא רווחים',
    confirmPasswordLabel: 'אימות סיסמה',
    confirmPasswordPlaceholder: 'הזן שוב את הסיסמה',
    acceptTerms: 'אני מסכים לתנאים',
    registerSubmit: 'צור חשבון',
    registerSubmitting: 'יוצר...',
    registerErrorDefault: 'שגיאת הרשמה',
    alreadyHasAccount: 'כבר יש לך חשבון?',
    signIn: 'התחבר',

    dashboardNavAria: 'ניווט ראשי',
    navOverview: 'סקירה',
    navLessons: 'שיעורים',
    navProgress: 'התקדמות',
    navSettings: 'הגדרות',
    logout: 'התנתק',
    today: 'היום',
    hello: 'שלום',
    dashboardSubtitle: 'המשך ללמוד ועקוב אחרי מצב המערכת.',
    searchPlaceholder: 'חפש שיעור, מילה או דוח',
    systemOnline: 'המערכת פעילה',
    dayReadyTitle: 'יום הלמידה שלך מוכן',
    dayReadyDesc: '3 תרגילים קצרים וחזרה אחת על אוצר מילים ישמרו על הקצב ללא עומס.',
    continueLesson: 'המשך שיעור',
    statsAria: 'מדדים מרכזיים',
    activeLessons: 'שיעורים פעילים',
    weeklyProgress: 'התקדמות שבועית',
    security: 'אבטחה',
    newItems: '2 חדשים',
    zeroIncidents: '0 אירועים',
    recentActions: 'פעולות אחרונות',
    all: 'הכול',
    activity1Title: 'שיעור: דקדוק בסיסי',
    activity2Title: 'חזרה: אוצר מילים מודרני',
    activity3Title: 'מבחן: מונחים טכניים',
    twoHoursAgo: 'לפני שעתיים',
    yesterday: 'אתמול',
    threeDaysAgo: 'לפני 3 ימים',
    envStatusTitle: 'מצב הסביבה',
    updatedNow: 'עודכן עכשיו',
    stable: 'יציב',
    stableDesc: 'ה-API, מסד הנתונים ושירותי הלמידה מגיבים בטווח תקין.',
    adminTitle: 'מרכז ניהול',
    adminOperator: 'מפעיל מערכת',
    adminReady: 'קונסולת הניהול הראשית מוכנה לפקודות.',

    initAccess: 'אתחל גישה',
  },
};

interface LanguageContextType {
  language: Language;
  languageMode: Language | 'system';
  t: Translations;
  setLanguage: (lang: Language) => void;
  setLanguageMode: (mode: Language | 'system') => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

const LANGUAGE_STORAGE_KEY = 'ui_language';
const LANGUAGE_MODE_STORAGE_KEY = 'ui_language_mode';

const getScopedKey = (base: string, userId?: string | null) =>
  userId ? `${base}:${userId}` : base;

const detectBrowserLanguage = (): Language => {
  if (typeof window === 'undefined') {
    return 'en';
  }

  const browserLang = window.navigator.language.split('-')[0];
  if (browserLang === 'he') return 'he';
  if (browserLang === 'ru') return 'ru';
  return 'en';
};

const readStoredLanguageMode = (userId?: string | null): Language | 'system' => {
  if (typeof window === 'undefined') {
    return 'system';
  }

  const scoped = window.localStorage.getItem(getScopedKey(LANGUAGE_MODE_STORAGE_KEY, userId));
  const fallback = window.localStorage.getItem(LANGUAGE_MODE_STORAGE_KEY);
  const value = scoped || fallback;

  if (value === 'ru' || value === 'en' || value === 'he' || value === 'system') {
    return value;
  }

  return 'system';
};

const readStoredLanguage = (userId?: string | null): Language | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  const scoped = window.localStorage.getItem(getScopedKey(LANGUAGE_STORAGE_KEY, userId));
  const fallback = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  const value = scoped || fallback;

  if (value === 'ru' || value === 'en' || value === 'he') {
    return value;
  }

  return null;
};

const resolveLanguage = (mode: Language | 'system'): Language => {
  if (mode === 'system') {
    return detectBrowserLanguage();
  }

  return mode;
};

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  const [languageMode, setLanguageMode] = useState<Language | 'system'>(() => readStoredLanguageMode(null));
  const [language, setLanguageState] = useState<Language>(() => {
    const mode = readStoredLanguageMode(null);
    const storedLanguage = readStoredLanguage(null);
    if (mode !== 'system') return mode;
    return storedLanguage || detectBrowserLanguage();
  });

  useEffect(() => {
    const remoteMode = user?.ui_preferences?.languageMode;
    const remoteLanguage = user?.ui_preferences?.language;

    if (remoteMode === 'ru' || remoteMode === 'en' || remoteMode === 'he' || remoteMode === 'system') {
      setLanguageMode(remoteMode);
      setLanguage(resolveLanguage(remoteMode));
      return;
    }

    if (remoteLanguage === 'ru' || remoteLanguage === 'en' || remoteLanguage === 'he') {
      setLanguageMode(remoteLanguage);
      setLanguage(remoteLanguage);
      return;
    }

    const localMode = readStoredLanguageMode(user?.id ?? null);
    setLanguageMode(localMode);
    const localLanguage = localMode === 'system'
      ? (readStoredLanguage(user?.id ?? null) || detectBrowserLanguage())
      : localMode;
    setLanguage(localLanguage);
  }, [user?.id, user?.ui_preferences?.language, user?.ui_preferences?.languageMode]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(getScopedKey(LANGUAGE_MODE_STORAGE_KEY, user?.id ?? null), languageMode);
      window.localStorage.setItem(getScopedKey(LANGUAGE_STORAGE_KEY, user?.id ?? null), language);
    }

    if (typeof document !== 'undefined') {
      document.documentElement.lang = language;
      document.documentElement.dir = language === 'he' ? 'rtl' : 'ltr';
    }
  }, [language, languageMode, user?.id]);

  useEffect(() => {
    if (languageMode === 'system') {
      setLanguage(resolveLanguage('system'));
    }
  }, [languageMode]);

  const setLanguage = (lang: Language) => {
    setLanguageMode(lang);
    setLanguageState(lang);
  };

  const setLanguageModeSafe = (mode: Language | 'system') => {
    setLanguageMode(mode);
    setLanguageState(resolveLanguage(mode));
  };

  const t = translations[language];

  return (
    <LanguageContext.Provider value={{ language, languageMode, t, setLanguage, setLanguageMode: setLanguageModeSafe }}>
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
