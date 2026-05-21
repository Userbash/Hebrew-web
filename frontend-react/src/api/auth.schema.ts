import { z } from 'zod';

export const AuthSchema = z.object({
  email: z.string().email('Некорректный email'),
  password: z.string().min(6, 'Пароль должен содержать минимум 6 символов'),
  acceptTerms: z.boolean().refine((val) => val === true, {
    message: 'Вы должны принять условия использования',
  }),
});

export type AuthCredentials = z.infer<typeof AuthSchema>;
