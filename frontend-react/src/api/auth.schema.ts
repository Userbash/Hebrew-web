import { z } from 'zod';

const PASSWORD_RULES_TEXT = 'Минимум 12 символов, заглавная/строчная буква, цифра и спецсимвол, без пробелов';

export const LoginSchema = z.object({
  email: z.string().email('Некорректный email'),
  password: z.string().min(1, 'Пароль обязателен'),
});

const StrongPasswordSchema = z.string()
  .min(12, PASSWORD_RULES_TEXT)
  .max(128, PASSWORD_RULES_TEXT)
  .regex(/[A-Z]/, PASSWORD_RULES_TEXT)
  .regex(/[a-z]/, PASSWORD_RULES_TEXT)
  .regex(/[0-9]/, PASSWORD_RULES_TEXT)
  .regex(/[^A-Za-z0-9]/, PASSWORD_RULES_TEXT)
  .regex(/^\S+$/, PASSWORD_RULES_TEXT);

export const RegisterSchema = z.object({
  email: z.string().email('Некорректный email'),
  username: z.string()
    .min(3, 'Username должен быть не менее 3 символов')
    .max(50, 'Username должен быть не более 50 символов')
    .regex(/^[A-Za-z0-9_.-]+$/, 'Разрешены только буквы, цифры, ., _, -'),
  password: StrongPasswordSchema,
  confirmPassword: z.string(),
  acceptTerms: z.boolean().refine((val) => val === true, {
    message: 'Вы должны принять условия использования',
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Пароли не совпадают',
  path: ['confirmPassword'],
});

export const AuthSchema = RegisterSchema;

export type LoginCredentials = z.infer<typeof LoginSchema>;
export type AuthCredentials = z.infer<typeof RegisterSchema>;
