declare module 'i18next' {
  interface I18nLike {
    isInitialized: boolean;
    language: string;
    use: (plugin: unknown) => I18nLike;
    init: (options: unknown) => Promise<unknown>;
    changeLanguage: (language: string) => Promise<unknown>;
    t: (key: string, options?: Record<string, unknown>) => string;
  }

  const i18next: I18nLike;
  export default i18next;
}
