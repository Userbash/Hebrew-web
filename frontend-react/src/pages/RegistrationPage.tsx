import React from 'react';
import axios from 'axios';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Mail, Lock, Loader2, Eye, EyeOff, User } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { Alert, Button, Card, Col, Container, Form, InputGroup, Row } from 'react-bootstrap';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { getDefaultRouteForUser } from '../security/adminAccess';
import api from '../api/client';
import UiPreferencesControls from '../components/Layout/UiPreferencesControls';

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

interface RegisterErrorResponse {
  message?: string;
  field?: 'email' | 'username' | 'both';
  suggestions?: string[];
}

const RegistrationPage: React.FC = () => {
  const [showPassword, setShowPassword] = React.useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false);
  const [usernameSuggestions, setUsernameSuggestions] = React.useState<string[]>([]);
  const [globalError, setGlobalError] = React.useState('');
  const { t } = useLanguage();
  const { setUser } = useAuth();
  const navigate = useNavigate();

  const { register, handleSubmit, setError, setValue, formState: { errors, isSubmitting } } = useForm<RegistrationForm>({
    resolver: zodResolver(registrationSchema),
    defaultValues: { acceptTerms: true }
  });

  const onSubmit = async (data: RegistrationForm) => {
    setUsernameSuggestions([]);
    setGlobalError('');

    try {
      const response = await api.post('/auth/register', {
        email: data.email,
        password: data.password,
        confirmPassword: data.confirmPassword,
        username: data.username,
      });
      setUser(response.data);
      navigate(getDefaultRouteForUser(response.data), { replace: true });
    } catch (err: unknown) {
      const payload = axios.isAxiosError<RegisterErrorResponse>(err)
        ? err.response?.data
        : undefined;

      const message = payload?.message || t.registerErrorDefault;
      const hasSuggestions = Array.isArray(payload?.suggestions) && payload.suggestions.length > 0;

      if (payload?.field === 'both') {
        setError('email', { message });
        setError('username', { message });
        return;
      }

      if (payload?.field === 'username') {
        setError('username', { message });
        setUsernameSuggestions(hasSuggestions ? payload.suggestions!.slice(0, 8) : []);
        return;
      }

      if (payload?.field === 'email') {
        setError('email', { message });
        return;
      }

      setGlobalError(message);
    }
  };

  return (
    <main className="login-page school-landing-bg">
      <UiPreferencesControls className="login-topbar" />
      <Container>
        <Row className="align-items-center g-4">
          <Col lg={7}>
            <div className="login-copy">
              <div className="login-badge">Language School</div>
              <h1>{t.registerHeroTitle}</h1>
              <p>{t.registerHeroDesc}</p>
            </div>
          </Col>
          <Col lg={5}>
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
              <Card className="login-card">
                <Card.Body>
                  <div className="login-card-header">
                    <h2>{t.registerCardTitle}</h2>
                  </div>

                  <Form onSubmit={handleSubmit(onSubmit)} className="login-form">
                    <Form.Group>
                      <Form.Label>{t.usernameLabel}</Form.Label>
                      <InputGroup className="login-input-wrap">
                        <InputGroup.Text><User size={18} /></InputGroup.Text>
                        <Form.Control {...register('username')} type="text" placeholder={t.usernamePlaceholder} autoComplete="username" />
                      </InputGroup>
                      {errors.username && <div className="login-error mt-1">{errors.username.message}</div>}
                      {usernameSuggestions.length > 0 && (
                        <div className="login-card-kicker mt-1">
                          Варианты username: {usernameSuggestions.map((suggestion, index) => (
                            <button
                              key={suggestion}
                              type="button"
                              onClick={() => setValue('username', suggestion, { shouldDirty: true, shouldValidate: true })}
                              className="site-link-btn"
                            >
                              {suggestion}{index < usernameSuggestions.length - 1 ? ', ' : ''}
                            </button>
                          ))}
                        </div>
                      )}
                    </Form.Group>

                    <Form.Group>
                      <Form.Label>{t.emailLabel}</Form.Label>
                      <InputGroup className="login-input-wrap">
                        <InputGroup.Text><Mail size={18} /></InputGroup.Text>
                        <Form.Control {...register('email')} type="email" placeholder="name@example.com" autoComplete="email" />
                      </InputGroup>
                      {errors.email && <div className="login-error mt-1">{errors.email.message}</div>}
                    </Form.Group>

                    <Form.Group>
                      <Form.Label>{t.passwordLabel}</Form.Label>
                      <InputGroup className="login-input-wrap">
                        <InputGroup.Text><Lock size={18} /></InputGroup.Text>
                        <Form.Control {...register('password')} type={showPassword ? 'text' : 'password'} placeholder={t.registerPasswordPlaceholder} autoComplete="new-password" />
                        <Button type="button" variant="outline-secondary" onClick={() => setShowPassword(!showPassword)} className="login-password-toggle">
                          {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </Button>
                      </InputGroup>
                      <div className="login-card-kicker mt-1">{t.passwordRulesHint}</div>
                      {errors.password && <div className="login-error mt-1">{errors.password.message}</div>}
                    </Form.Group>

                    <Form.Group>
                      <Form.Label>{t.confirmPasswordLabel}</Form.Label>
                      <InputGroup className="login-input-wrap">
                        <InputGroup.Text><Lock size={18} /></InputGroup.Text>
                        <Form.Control {...register('confirmPassword')} type={showConfirmPassword ? 'text' : 'password'} placeholder={t.confirmPasswordPlaceholder} autoComplete="new-password" />
                        <Button type="button" variant="outline-secondary" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="login-password-toggle">
                          {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </Button>
                      </InputGroup>
                      {errors.confirmPassword && <div className="login-error mt-1">{errors.confirmPassword.message}</div>}
                    </Form.Group>

                    <Form.Check type="checkbox" className="small" label={t.acceptTerms} {...register('acceptTerms')} />
                    {errors.acceptTerms && <div className="login-error mt-1">{errors.acceptTerms.message}</div>}
                    {globalError && <Alert variant="danger" className="py-2 mb-0">{globalError}</Alert>}

                    <Button type="submit" disabled={isSubmitting} className="login-submit d-inline-flex justify-content-center align-items-center gap-2">
                      {isSubmitting ? <Loader2 className="spin" /> : t.registerSubmit}
                    </Button>
                  </Form>

                  <div className="login-footer-link">
                    {t.alreadyHasAccount} <Link to="/login">{t.signIn}</Link>
                  </div>
                </Card.Body>
              </Card>
            </motion.div>
          </Col>
        </Row>
      </Container>
    </main>
  );
};

export default RegistrationPage;
