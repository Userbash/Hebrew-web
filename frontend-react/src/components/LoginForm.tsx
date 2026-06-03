import { useState, type FormEvent } from 'react';
import { Eye, EyeOff, Lock, Mail } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { Alert, Button, Card, Form, InputGroup } from 'react-bootstrap';
import { useLanguage } from '../context/LanguageContext';
import axios from 'axios';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { getDefaultRouteForUser } from '../security/adminAccess';
import UiPreferencesControls from './Layout/UiPreferencesControls';

export default function LoginForm() {
  const { t } = useLanguage();
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
      navigate(getDefaultRouteForUser(response.data), { replace: true });
    } catch (err: unknown) {
      const message = axios.isAxiosError<{ message?: string }>(err)
        ? err.response?.data?.message
        : undefined;
      setError(message || t.loginErrorDefault);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="login-page auth-portal-page">
      <header className="auth-portal-nav">
        <Link to="/" className="language-brand" aria-label="Ulpan Hebrew 2026 home">
          <span className="language-brand__mark">ע</span>
          <span>Ulpan Hebrew 2026</span>
        </Link>
        <UiPreferencesControls className="login-topbar" />
      </header>

      <section className="auth-portal-shell" aria-label="Authorization portal">
        <div className="login-copy">
          <div className="login-badge">Hebrew learning portal</div>
          <h1>{t.loginHeroTitle}</h1>
          <p>{t.loginHeroDesc}</p>
          <div className="auth-portal-points" aria-label="Authorization benefits">
            <span>Personal cabinet</span>
            <span>Progress tracking</span>
            <span>Secure sessions</span>
          </div>
        </div>

        <motion.div className="auth-card-motion" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="login-card">
            <Card.Body>
              <div className="login-card-header">
                <span className="login-card-kicker">{t.loginCardKicker}</span>
                <h2>{t.loginCardTitle}</h2>
                <p>{t.loginCardDesc}</p>
              </div>

              <Form onSubmit={handleSubmit} className="login-form">
                <Form.Group>
                  <Form.Label>{t.emailLabel}</Form.Label>
                  <InputGroup className="login-input-wrap">
                    <InputGroup.Text><Mail size={18} /></InputGroup.Text>
                    <Form.Control
                      type="email"
                      name="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@example.com"
                      autoComplete="email"
                      required
                    />
                  </InputGroup>
                </Form.Group>

                <Form.Group>
                  <Form.Label>{t.passwordLabel}</Form.Label>
                  <InputGroup className="login-input-wrap">
                    <InputGroup.Text><Lock size={18} /></InputGroup.Text>
                    <Form.Control
                      type={showPassword ? 'text' : 'password'}
                      name="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={t.passwordPlaceholder}
                      autoComplete="current-password"
                      minLength={1}
                      required
                    />
                    <Button
                      type="button"
                      variant="outline-secondary"
                      onClick={() => setShowPassword((value) => !value)}
                      className="login-password-toggle"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </Button>
                  </InputGroup>
                </Form.Group>

                {error && <Alert variant="danger" className="py-2 mb-0" role="alert">{error}</Alert>}

                <Button type="submit" className="login-submit" disabled={isSubmitting}>
                  {isSubmitting ? t.loginSubmitting : t.login}
                </Button>
              </Form>

              <div className="login-footer-link">
                {t.noAccount} <Link to="/register">{t.createAccess}</Link>
              </div>
              <Link to="/" className="auth-back-link">Back to public portal</Link>
            </Card.Body>
          </Card>
        </motion.div>
      </section>
    </main>
  );
}
