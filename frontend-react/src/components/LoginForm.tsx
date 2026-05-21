import { useState, type FormEvent } from 'react';
import { Eye, EyeOff, Lock, Mail, Moon, Sun } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import axios from 'axios';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function LoginForm() {
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage } = useLanguage();
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const response = await api.post('/auth/login', { email, password });
      setUser(response.data);
      navigate(response.data.role === 'admin' ? '/admin' : '/dashboard', { replace: true });
    } catch (err: unknown) {
      const message = axios.isAxiosError<{ message?: string }>(err)
        ? err.response?.data?.message
        : undefined;
      setError(message || 'Не удалось войти. Проверьте email и пароль.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="login-page">
      <div className="login-topbar" aria-label="Настройки входа">
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value as 'en' | 'ru' | 'he')}
          className="login-select"
          aria-label="Язык интерфейса"
        >
          <option value="en">English</option>
          <option value="ru">Русский</option>
          <option value="he">עברית</option>
        </select>
        <button onClick={toggleTheme} className="login-icon-button" aria-label="Переключить тему">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>

      <section className="login-layout">
        <div className="login-copy">
          <div className="login-badge">Hebrew AI</div>
          <h1>Учите иврит в понятном рабочем кабинете</h1>
          <p>
            Войдите, чтобы продолжить уроки, повторить слова и посмотреть прогресс без лишних панелей и сложных настроек.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="login-card"
        >
          <div className="login-card-header">
            <span className="login-card-kicker">Личный кабинет</span>
            <h2>Вход</h2>
            <p>Используйте email и пароль аккаунта.</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <label className="login-field">
              <span>Email</span>
              <div className="login-input-wrap">
                <Mail size={18} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  autoComplete="email"
                  required
                />
              </div>
            </label>

            <label className="login-field">
              <span>Пароль</span>
              <div className="login-input-wrap">
                <Lock size={18} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Минимум 6 символов"
                  autoComplete="current-password"
                  minLength={6}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="login-password-toggle"
                  aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </label>

            {error && <p className="login-error" role="alert">{error}</p>}

            <button type="submit" className="login-submit" disabled={isSubmitting}>
              {isSubmitting ? 'Вход...' : 'Войти'}
            </button>
          </form>

          <div className="login-footer-link">
            Нет аккаунта? <Link to="/register">Создать доступ</Link>
          </div>
        </motion.div>
      </section>
    </main>
  );
}
