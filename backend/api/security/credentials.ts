const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const USERNAME_REGEX = /^[A-Za-z0-9_.-]{3,50}$/;

export const PASSWORD_MIN_LENGTH = 12;
export const PASSWORD_MAX_LENGTH = 128;

const COMMON_PASSWORDS = new Set([
    'password',
    'password123',
    'qwerty123',
    '12345678',
    '123456789',
    'admin123',
    'letmein',
    'welcome123',
    'iloveyou',
]);

export interface PasswordValidationResult {
    valid: boolean;
    errors: string[];
}

export const normalizeEmail = (email: string) => email.trim().toLowerCase();

export const isValidEmail = (email: string) => EMAIL_REGEX.test(email);

export const normalizeUsername = (username: string) => username.trim();

export const isValidUsername = (username: string) => USERNAME_REGEX.test(username);

export const validatePassword = (password: string, context?: { username?: string; email?: string }): PasswordValidationResult => {
    const errors: string[] = [];

    if (password.length < PASSWORD_MIN_LENGTH) {
        errors.push(`Пароль должен быть не менее ${PASSWORD_MIN_LENGTH} символов`);
    }

    if (password.length > PASSWORD_MAX_LENGTH) {
        errors.push(`Пароль должен быть не более ${PASSWORD_MAX_LENGTH} символов`);
    }

    if (!/[a-z]/.test(password)) {
        errors.push('Пароль должен содержать строчную букву');
    }

    if (!/[A-Z]/.test(password)) {
        errors.push('Пароль должен содержать заглавную букву');
    }

    if (!/[0-9]/.test(password)) {
        errors.push('Пароль должен содержать цифру');
    }

    if (!/[^A-Za-z0-9]/.test(password)) {
        errors.push('Пароль должен содержать спецсимвол');
    }

    if (/\s/.test(password)) {
        errors.push('Пароль не должен содержать пробелы');
    }

    if (/(.)\1{3,}/.test(password)) {
        errors.push('Пароль не должен содержать длинные повторяющиеся последовательности символов');
    }

    const lowered = password.toLowerCase();
    if (COMMON_PASSWORDS.has(lowered)) {
        errors.push('Пароль слишком простой');
    }

    const username = context?.username?.toLowerCase();
    if (username && username.length > 2 && lowered.includes(username)) {
        errors.push('Пароль не должен содержать имя пользователя');
    }

    const emailLocalPart = context?.email?.split('@')[0]?.toLowerCase();
    if (emailLocalPart && emailLocalPart.length > 2 && lowered.includes(emailLocalPart)) {
        errors.push('Пароль не должен содержать часть email');
    }

    return {
        valid: errors.length === 0,
        errors,
    };
};

export const PASSWORD_RULES_TEXT = [
    `Минимум ${PASSWORD_MIN_LENGTH} символов`,
    'Хотя бы 1 строчная буква',
    'Хотя бы 1 заглавная буква',
    'Хотя бы 1 цифра',
    'Хотя бы 1 спецсимвол',
    'Без пробелов',
].join(', ');
