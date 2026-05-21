import React from 'react';
import axios from 'axios';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Mail, Lock, Loader2, Eye, EyeOff, User } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';

const registrationSchema = z.object({
  email: z.string().email('Некорректный email'),
  username: z.string()
    .min(3, 'Username должен быть не менее 3 символов')
    .max(50, 'Username должен быть не более 50 символов')
    .regex(/^[A-Za-z0-9_.-]+$/, 'Разрешены только буквы, цифры, ., _, -'),
  password: z.string()
    .min(12, 'Пароль должен быть не менее 12 символов')
    .max(128, 'Пароль должен быть не более 128 символов')
    .regex(/[A-Z]/, 'Добавьте заглавную букву')
    .regex(/[a-z]/, 'Добавьте строчную букву')
    .regex(/[0-9]/, 'Добавьте цифру')
    .regex(/[^A-Za-z0-9]/, 'Добавьте спецсимвол')
    .regex(/^\S+$/, 'Пароль не должен содержать пробелы'),
  confirmPassword: z.string(),
  acceptTerms: z.literal(true, { message: 'Необходимо согласиться с условиями' }),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Пароли не совпадают',
  path: ['confirmPassword'],
});

type RegistrationForm = z.infer<typeof registrationSchema>;

const RegistrationPage: React.FC = () => {
  const [showPassword, setShowPassword] = React.useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false);
  const { language, setLanguage, t } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const { setUser } = useAuth();
  const navigate = useNavigate();

  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<RegistrationForm>({
    resolver: zodResolver(registrationSchema),
    defaultValues: { acceptTerms: true }
  });

  const onSubmit = async (data: RegistrationForm) => {
    try {
      const response = await api.post('/auth/register', {
        email: data.email,
        password: data.password,
        confirmPassword: data.confirmPassword,
        username: data.username,
      });
      setUser(response.data);
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      const message = axios.isAxiosError<{ message?: string }>(err)
        ? err.response?.data?.message
        : undefined;

      setError('email', { message: message || t.registerErrorDefault });
    }
  };

  return (
    <main className="login-page">
      <div className="login-topbar">
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value as 'en' | 'ru' | 'he')}
          className="login-select"
          aria-label={t.languageAria}
        >
          <option value="en">English</option>
          <option value="ru">Русский</option>
          <option value="he">עברית</option>
        </select>
        <button onClick={toggleTheme} className="login-icon-button" aria-label={t.toggleThemeAria}>
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>

      <section className="login-layout">
        <div className="login-copy">
          <div className="login-badge">Hebrew AI</div>
          <h1>{t.registerHeroTitle}</h1>
          <p>{t.registerHeroDesc}</p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="login-card"
        >
          <div className="login-card-header">
            <h2>{t.registerCardTitle}</h2>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="login-form">
            <label className="login-field">
              <span>{t.usernameLabel}</span>
              <div className="login-input-wrap">
                <User size={18} />
                <input {...register('username')} type="text" placeholder={t.usernamePlaceholder} autoComplete="username" />
              </div>
              {errors.username && <p className="login-error">{errors.username.message}</p>}
            </label>

            <label className="login-field">
              <span>{t.emailLabel}</span>
              <div className="login-input-wrap">
                <Mail size={18} />
                <input {...register('email')} type="email" placeholder="name@example.com" autoComplete="email" />
              </div>
              {errors.email && <p className="login-error">{errors.email.message}</p>}
            </label>

            <label className="login-field">
              <span>{t.passwordLabel}</span>
              <div className="login-input-wrap">
                <Lock size={18} />
                <input {...register('password')} type={showPassword ? 'text' : 'password'} placeholder={t.registerPasswordPlaceholder} autoComplete="new-password" />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="login-password-toggle">
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <p className="login-card-kicker">{t.passwordRulesHint}</p>
              {errors.password && <p className="login-error">{errors.password.message}</p>}
            </label>

            <label className="login-field">
              <span>{t.confirmPasswordLabel}</span>
              <div className="login-input-wrap">
                <Lock size={18} />
                <input {...register('confirmPassword')} type={showConfirmPassword ? 'text' : 'password'} placeholder={t.confirmPasswordPlaceholder} autoComplete="new-password" />
                <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="login-password-toggle">
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.confirmPassword && <p className="login-error">{errors.confirmPassword.message}</p>}
            </label>

            <label className="flex items-center gap-2 text-sm text-slate-500 font-bold">
              <input type="checkbox" {...register('acceptTerms')} className="accent-blue-600" />
              {t.acceptTerms}
            </label>
            {errors.acceptTerms && <p className="login-error">{errors.acceptTerms.message}</p>}

            <button type="submit" disabled={isSubmitting} className="login-submit">
              {isSubmitting ? <Loader2 className="animate-spin" /> : t.registerSubmit}
            </button>
          </form>

          <div className="login-footer-link">
            {t.alreadyHasAccount} <Link to="/login">{t.signIn}</Link>
          </div>
        </motion.div>
      </section>
    </main>
  );
};

export default RegistrationPage;
