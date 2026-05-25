import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import i18next from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { useAuth } from './AuthContext';

export type Language = 'ru' | 'en' | 'he';

interface Translations {
  [key: string]: string;

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

  publicKicker: string;
  publicTitle: string;
  publicDesc: string;
  publicBrowse: string;
  publicCard1Title: string;
  publicCard1Desc: string;
  publicCard2Title: string;
  publicCard2Desc: string;
  publicCard3Title: string;
  publicCard3Desc: string;

  publicationsKicker: string;
  publicationsTitle: string;
  publicationsDesc: string;
  publicationsLoading: string;
  publicationsLoadError: string;
  publicationsEmpty: string;
  publicationsNoDesc: string;
  publicationsBack: string;
  publicationsStatusPublished: string;

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
    loginHeroTitle: 'Изучайте языки в удобном учебном кабинете',
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
    registerHeroTitle: 'Изучайте языки в удобном учебном кабинете',
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
    publicKicker: 'Платформа Language School',
    publicTitle: 'Единый публичный сайт, личный кабинет и админ-панель',
    publicDesc: 'Единая дизайн-система, централизованное управление контентом, RBAC-модель доступа и безопасный процесс модерации.',
    publicBrowse: 'Смотреть публикации',
    publicCard1Title: 'Публичный сайт',
    publicCard1Desc: 'SEO-страницы только с опубликованными и публичными материалами.',
    publicCard2Title: 'Личный кабинет',
    publicCard2Desc: 'Рабочее пространство пользователя с управлением профилем и доступом.',
    publicCard3Title: 'Админ-управление',
    publicCard3Desc: 'Управление пользователями, ролями, правами, модерацией и аудитом.',
    publicationsKicker: 'Публичный каталог',
    publicationsTitle: 'Опубликованный контент',
    publicationsDesc: 'Публичные материалы, прошедшие модерацию.',
    publicationsLoading: 'Загрузка...',
    publicationsLoadError: 'Не удалось загрузить публикации',
    publicationsEmpty: 'Пока нет опубликованного контента.',
    publicationsNoDesc: 'Без описания',
    publicationsBack: 'Назад на главную',
    publicationsStatusPublished: 'опубликовано',
    adminNavDashboard: 'Панель',
    adminNavUsers: 'Пользователи',
    adminNavGroupsAccess: 'Группы и доступ',
    adminNavContentModeration: 'Модерация контента',
    adminNavAuditLogs: 'Аудит и логи',
    adminSectionOverviewHealth: 'Обзор и состояние',
    adminSectionMapLogging: 'Карта админа и логирование',
    adminSectionSystemMonitoring: 'Мониторинг системы',
    adminSectionDirectory: 'Каталог',
    adminSectionCreateUser: 'Создать пользователя',
    adminSectionGroupsCatalog: 'Каталог групп',
    adminSectionUserAssignments: 'Назначения пользователей',
    adminSectionPublicationsQueue: 'Очередь публикаций',
    adminSectionAuditTrail: 'Журнал изменений',
    adminSectionApiLogs: 'Логи API',
    adminConsole: 'Админ-консоль',
    adminSecureGovernance: 'Безопасное управление',
    adminOperatorLabel: 'Оператор',
    adminNoRoles: 'нет ролей',
    adminExit: 'Выход из админки',
    adminAttentionNow: 'Что требует внимания сейчас',
    adminNoCriticalSignals: 'Критичных сигналов нет',
    adminProcessingSecureRequest: 'Обработка защищенного запроса...',
    adminSectionPurpose: 'Назначение раздела',
    adminProfileQuickMap: 'Быстрая карта профиля',
    initAccess: 'Инициализировать доступ',
  },
  en: {
    welcome: 'Welcome Back!', username: 'Username or Email', password: 'Password', login: 'Sign In', cancel: 'Cancel', rememberMe: 'Remember Me', forgotPassword: 'Forgot password?', settings: 'Settings',
    loginSettingsAria: 'Login settings', languageAria: 'Interface language', languageSystem: 'System', toggleThemeAria: 'Toggle theme', themeSystem: 'System', themeLight: 'Light', themeDark: 'Dark',
    loginHeroTitle: 'Learn languages in a clear workspace', loginHeroDesc: 'Sign in to continue lessons, review words, and track progress without extra complexity.', loginCardKicker: 'Personal account', loginCardTitle: 'Sign In', loginCardDesc: 'Use your account email and password.',
    emailLabel: 'Email', passwordLabel: 'Password', passwordPlaceholder: 'Enter password', loginSubmitting: 'Signing in...', loginErrorDefault: 'Could not sign in. Check your email and password.', noAccount: 'No account?', createAccess: 'Create access',
    registerHeroTitle: 'Learn languages in a clear workspace', registerHeroDesc: 'Create an account to start learning.', registerCardTitle: 'Sign Up', usernameLabel: 'Username', usernamePlaceholder: 'For example: john.doe', registerPasswordPlaceholder: 'Enter a strong password', passwordRulesHint: 'At least 12 chars, upper/lowercase, number, special char, no spaces', confirmPasswordLabel: 'Confirm password', confirmPasswordPlaceholder: 'Repeat password', acceptTerms: 'I agree to the terms', registerSubmit: 'Create account', registerSubmitting: 'Creating...', registerErrorDefault: 'Registration error', alreadyHasAccount: 'Already have an account?', signIn: 'Sign In',
    dashboardNavAria: 'Main navigation', navOverview: 'Overview', navLessons: 'Lessons', navProgress: 'Progress', navSettings: 'Settings', logout: 'Log out', today: 'Today', hello: 'Hello', dashboardSubtitle: 'Continue learning and monitor platform status.', searchPlaceholder: 'Find lesson, word, or report', systemOnline: 'System online', dayReadyTitle: 'Your learning day is ready', dayReadyDesc: '3 short exercises and one vocabulary review will keep your pace without overload.', continueLesson: 'Continue lesson', statsAria: 'Key metrics', activeLessons: 'Active lessons', weeklyProgress: 'Weekly progress', security: 'Security', newItems: '2 new', zeroIncidents: '0 incidents', recentActions: 'Recent activity', all: 'All', activity1Title: 'Lesson: basic grammar', activity2Title: 'Review: modern vocabulary', activity3Title: 'Test: technical terms', twoHoursAgo: '2 hours ago', yesterday: 'Yesterday', threeDaysAgo: '3 days ago', envStatusTitle: 'Environment status', updatedNow: 'Updated now', stable: 'Stable', stableDesc: 'API, database, and learning services respond within normal range.', adminTitle: 'Admin control center', adminOperator: 'System operator', adminReady: 'Main administrative console is ready for commands.',
    publicKicker: 'Language School Platform', publicTitle: 'Unified Public Website, Client Cabinet, and Admin Panel', publicDesc: 'Single design system, centralized content governance, RBAC access model, and secure moderation workflow.', publicBrowse: 'Browse Publications', publicCard1Title: 'Public Website', publicCard1Desc: 'SEO-friendly content pages with only published and public materials.', publicCard2Title: 'Client Cabinet', publicCard2Desc: 'Authorized user workspace with ownership-aware access and profile control.', publicCard3Title: 'Admin Governance', publicCard3Desc: 'Admin panel controls users, roles, rights, moderation, and audit trails.',
    publicationsKicker: 'Public Catalog', publicationsTitle: 'Published Content', publicationsDesc: 'Public materials approved by moderation workflow.', publicationsLoading: 'Loading...', publicationsLoadError: 'Failed to load publications', publicationsEmpty: 'No published content yet.', publicationsNoDesc: 'No description', publicationsBack: 'Back to Home', publicationsStatusPublished: 'published',
    adminNavDashboard: 'Dashboard',
    adminNavUsers: 'Users',
    adminNavGroupsAccess: 'Groups & access',
    adminNavContentModeration: 'Content moderation',
    adminNavAuditLogs: 'Audit & logs',
    adminSectionOverviewHealth: 'Overview & health',
    adminSectionMapLogging: 'Admin map & logging',
    adminSectionSystemMonitoring: 'System monitoring',
    adminSectionDirectory: 'Directory',
    adminSectionCreateUser: 'Create user',
    adminSectionGroupsCatalog: 'Groups catalog',
    adminSectionUserAssignments: 'User assignments',
    adminSectionPublicationsQueue: 'Publications queue',
    adminSectionAuditTrail: 'Change audit trail',
    adminSectionApiLogs: 'API activity logs',
    adminConsole: 'Admin Console',
    adminSecureGovernance: 'Secure governance',
    adminOperatorLabel: 'Operator',
    adminNoRoles: 'no roles',
    adminExit: 'Exit admin',
    adminAttentionNow: 'What needs attention now',
    adminNoCriticalSignals: 'No critical signals',
    adminProcessingSecureRequest: 'Processing secured request...',
    adminSectionPurpose: 'What this section is for',
    adminProfileQuickMap: 'Profile quick map',
    initAccess: 'Initialize access',
  },
  he: {
    welcome: 'ברוך הבא!', username: 'שם משתמש או אימייל', password: 'סיסמה', login: 'התחברות', cancel: 'ביטול', rememberMe: 'זכור אותי', forgotPassword: 'שכחת סיסמה?', settings: 'הגדרות',
    loginSettingsAria: 'הגדרות התחברות', languageAria: 'שפת ממשק', languageSystem: 'מערכת', toggleThemeAria: 'החלף ערכת נושא', themeSystem: 'מערכת', themeLight: 'בהיר', themeDark: 'כהה',
    loginHeroTitle: 'למד שפות בסביבת עבודה ברורה', loginHeroDesc: 'התחבר כדי להמשיך שיעורים, לחזור על מילים ולעקוב אחרי ההתקדמות בלי עומס מיותר.', loginCardKicker: 'אזור אישי', loginCardTitle: 'התחברות', loginCardDesc: 'השתמש באימייל ובסיסמה של החשבון שלך.',
    emailLabel: 'אימייל', passwordLabel: 'סיסמה', passwordPlaceholder: 'הזן סיסמה', loginSubmitting: 'מתחבר...', loginErrorDefault: 'ההתחברות נכשלה. בדוק אימייל וסיסמה.', noAccount: 'אין לך חשבון?', createAccess: 'צור גישה',
    registerHeroTitle: 'למד שפות בסביבת עבודה ברורה', registerHeroDesc: 'צור חשבון כדי להתחיל ללמוד.', registerCardTitle: 'הרשמה', usernameLabel: 'שם משתמש', usernamePlaceholder: 'לדוגמה: daniel.levi', registerPasswordPlaceholder: 'הזן סיסמה חזקה', passwordRulesHint: 'לפחות 12 תווים, אות גדולה/קטנה, מספר, תו מיוחד, ללא רווחים', confirmPasswordLabel: 'אימות סיסמה', confirmPasswordPlaceholder: 'הזן שוב את הסיסמה', acceptTerms: 'אני מסכים לתנאים', registerSubmit: 'צור חשבון', registerSubmitting: 'יוצר...', registerErrorDefault: 'שגיאת הרשמה', alreadyHasAccount: 'כבר יש לך חשבון?', signIn: 'התחבר',
    dashboardNavAria: 'ניווט ראשי', navOverview: 'סקירה', navLessons: 'שיעורים', navProgress: 'התקדמות', navSettings: 'הגדרות', logout: 'התנתק', today: 'היום', hello: 'שלום', dashboardSubtitle: 'המשך ללמוד ועקוב אחרי מצב המערכת.', searchPlaceholder: 'חפש שיעור, מילה או דוח', systemOnline: 'המערכת פעילה', dayReadyTitle: 'יום הלמידה שלך מוכן', dayReadyDesc: '3 תרגילים קצרים וחזרה אחת על אוצר מילים ישמרו על הקצב ללא עומס.', continueLesson: 'המשך שיעור', statsAria: 'מדדים מרכזיים', activeLessons: 'שיעורים פעילים', weeklyProgress: 'התקדמות שבועית', security: 'אבטחה', newItems: '2 חדשים', zeroIncidents: '0 אירועים', recentActions: 'פעולות אחרונות', all: 'הכול', activity1Title: 'שיעור: דקדוק בסיסי', activity2Title: 'חזרה: אוצר מילים מודרני', activity3Title: 'מבחן: מונחים טכניים', twoHoursAgo: 'לפני שעתיים', yesterday: 'אתמול', threeDaysAgo: 'לפני 3 ימים', envStatusTitle: 'מצב הסביבה', updatedNow: 'עודכן עכשיו', stable: 'יציב', stableDesc: 'ה-API, מסד הנתונים ושירותי הלמידה מגיבים בטווח תקין.', adminTitle: 'מרכז ניהול', adminOperator: 'מפעיל מערכת', adminReady: 'קונסולת הניהול הראשית מוכנה לפקודות.',
    publicKicker: 'פלטפורמת Language School', publicTitle: 'אתר ציבורי, אזור אישי ופאנל ניהול מאוחדים', publicDesc: 'מערכת עיצוב אחת, ניהול תוכן מרכזי, מודל גישה RBAC ותהליך מודרציה מאובטח.', publicBrowse: 'עיון בפרסומים', publicCard1Title: 'אתר ציבורי', publicCard1Desc: 'עמודי SEO עם חומרים שפורסמו לציבור בלבד.', publicCard2Title: 'אזור אישי', publicCard2Desc: 'סביבת עבודה למשתמש עם גישה וניהול פרופיל.', publicCard3Title: 'ניהול אדמין', publicCard3Desc: 'ניהול משתמשים, תפקידים, הרשאות, מודרציה וביקורת.',
    publicationsKicker: 'קטלוג ציבורי', publicationsTitle: 'תוכן שפורסם', publicationsDesc: 'חומרים ציבוריים שאושרו בתהליך המודרציה.', publicationsLoading: 'טוען...', publicationsLoadError: 'טעינת פרסומים נכשלה', publicationsEmpty: 'עדיין אין תוכן שפורסם.', publicationsNoDesc: 'ללא תיאור', publicationsBack: 'חזרה לדף הבית', publicationsStatusPublished: 'פורסם',
    adminNavDashboard: 'לוח בקרה',
    adminNavUsers: 'משתמשים',
    adminNavGroupsAccess: 'קבוצות והרשאות',
    adminNavContentModeration: 'ניהול תוכן',
    adminNavAuditLogs: 'ביקורת ולוגים',
    adminSectionOverviewHealth: 'סקירה ומצב',
    adminSectionMapLogging: 'מפת ניהול ולוגים',
    adminSectionSystemMonitoring: 'ניטור מערכת',
    adminSectionDirectory: 'ספרייה',
    adminSectionCreateUser: 'יצירת משתמש',
    adminSectionGroupsCatalog: 'קטלוג קבוצות',
    adminSectionUserAssignments: 'שיוכי משתמשים',
    adminSectionPublicationsQueue: 'תור פרסומים',
    adminSectionAuditTrail: 'יומן שינויים',
    adminSectionApiLogs: 'לוגים של API',
    adminConsole: 'קונסולת ניהול',
    adminSecureGovernance: 'ממשל מאובטח',
    adminOperatorLabel: 'מפעיל',
    adminNoRoles: 'ללא תפקידים',
    adminExit: 'יציאה מניהול',
    adminAttentionNow: 'מה דורש תשומת לב כעת',
    adminNoCriticalSignals: 'אין התראות קריטיות',
    adminProcessingSecureRequest: 'מעבד בקשה מאובטחת...',
    adminSectionPurpose: 'מטרת הסעיף',
    adminProfileQuickMap: 'מפת פרופיל מהירה',
    initAccess: 'אתחל גישה',
  },
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

if (!i18next.isInitialized) {
  void i18next
    .use(LanguageDetector)
    .init({
      resources: {
        ru: { translation: translations.ru },
        en: { translation: translations.en },
        he: { translation: translations.he },
      },
      fallbackLng: 'en',
      lng: detectSystemLanguage(),
      detection: {
        order: ['localStorage', 'cookie', 'navigator'],
        lookupLocalStorage: 'ui_language',
        lookupCookie: 'ui_language',
        caches: ['localStorage', 'cookie'],
      },
      interpolation: { escapeValue: false },
    });
}

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
const getScopedKey = (base: string, userId?: string | null) => (userId ? `${base}:${userId}` : base);

const readStoredLanguageMode = (userId?: string | null): Language | 'system' => {
  if (typeof window === 'undefined') return 'system';
  const scoped = window.localStorage.getItem(getScopedKey(LANGUAGE_MODE_STORAGE_KEY, userId));
  const fallback = window.localStorage.getItem(LANGUAGE_MODE_STORAGE_KEY);
  const value = scoped || fallback;
  if (value === 'ru' || value === 'en' || value === 'he' || value === 'system') return value;
  return 'system';
};

const readStoredLanguage = (userId?: string | null): Language | null => {
  if (typeof window === 'undefined') return null;
  const scoped = window.localStorage.getItem(getScopedKey(LANGUAGE_STORAGE_KEY, userId));
  const fallback = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  const value = scoped || fallback;
  if (value === 'ru' || value === 'en' || value === 'he') return value;
  return null;
};

const resolveLanguage = (mode: Language | 'system'): Language => (mode === 'system' ? detectSystemLanguage() : mode);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [languageMode, setLanguageMode] = useState<Language | 'system'>(() => readStoredLanguageMode(null));
  const [language, setLanguageState] = useState<Language>(() => {
    const mode = readStoredLanguageMode(null);
    const storedLanguage = readStoredLanguage(null);
    if (mode !== 'system') return mode;
    return storedLanguage || detectSystemLanguage();
  });

  useEffect(() => {
    const remoteMode = user?.ui_preferences?.languageMode;
    const remoteLanguage = user?.ui_preferences?.language;

    if (remoteMode === 'ru' || remoteMode === 'en' || remoteMode === 'he' || remoteMode === 'system') {
      setLanguageMode(remoteMode);
      setLanguageState(resolveLanguage(remoteMode));
      return;
    }

    if (remoteLanguage === 'ru' || remoteLanguage === 'en' || remoteLanguage === 'he') {
      setLanguageMode(remoteLanguage);
      setLanguageState(remoteLanguage);
      return;
    }

    const localMode = readStoredLanguageMode(user?.id ?? null);
    setLanguageMode(localMode);
    const localLanguage = localMode === 'system' ? (readStoredLanguage(user?.id ?? null) || detectSystemLanguage()) : localMode;
    setLanguageState(localLanguage);
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

    if (i18next.language !== language) {
      void i18next.changeLanguage(language);
    }
  }, [language, languageMode, user?.id]);

  useEffect(() => {
    if (typeof window === 'undefined' || languageMode !== 'system') return;
    const handleLanguageChange = () => setLanguageState(detectSystemLanguage());
    window.addEventListener('languagechange', handleLanguageChange);
    return () => window.removeEventListener('languagechange', handleLanguageChange);
  }, [languageMode]);

  const setLanguage = (lang: Language) => {
    setLanguageMode(lang);
    setLanguageState(lang);
  };

  const setLanguageModeSafe = (mode: Language | 'system') => {
    setLanguageMode(mode);
    setLanguageState(resolveLanguage(mode));
  };

  const t = useMemo<Translations>(() => {
    const keys = Object.keys(translations.en) as Array<keyof Translations>;
    return keys.reduce((acc, key) => {
      acc[key] = i18next.t(key as string, { lng: language, defaultValue: translations.en[key] });
      return acc;
    }, {} as Translations);
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, languageMode, t, setLanguage, setLanguageMode: setLanguageModeSafe }}>
      <div dir={language === 'he' ? 'rtl' : 'ltr'}>{children}</div>
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
