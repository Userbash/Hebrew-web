import React, { createContext, useContext, useEffect, useState } from 'react';

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
  toggleThemeAria: string;
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
    toggleThemeAria: 'Переключить тему',
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
    toggleThemeAria: 'Toggle theme',
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
    toggleThemeAria: 'החלף ערכת נושא',
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
  t: Translations;
  setLanguage: (lang: Language) => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

const LANGUAGE_STORAGE_KEY = 'ui_language';

const getInitialLanguage = (): Language => {
  if (typeof window === 'undefined') {
    return 'en';
  }

  const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (stored === 'ru' || stored === 'en' || stored === 'he') {
    return stored;
  }

  const browserLang = window.navigator.language.split('-')[0];
  if (browserLang === 'he') return 'he';
  if (browserLang === 'ru') return 'ru';
  return 'en';
};

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>(getInitialLanguage);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    }

    if (typeof document !== 'undefined') {
      document.documentElement.lang = language;
      document.documentElement.dir = language === 'he' ? 'rtl' : 'ltr';
    }
  }, [language]);

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
