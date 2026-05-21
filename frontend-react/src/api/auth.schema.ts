import { z } from 'zod';

export const LoginSchema = z.object({
  email: z.string().email('Некорректный email'),
  password: z.string().min(6, 'Пароль должен содержать минимум 6 символов'),
});

export const RegisterSchema = LoginSchema.extend({
  acceptTerms: z.boolean().refine((val) => val === true, {
    message: 'Вы должны принять условия использования',
  }),
});

export const AuthSchema = RegisterSchema;

export type LoginCredentials = z.infer<typeof LoginSchema>;
export type AuthCredentials = z.infer<typeof RegisterSchema>;
