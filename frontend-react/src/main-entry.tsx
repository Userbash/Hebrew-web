import { lazy, StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App } from './App.tsx';
import AdminGuard from './components/AdminGuard';
import AuthGuard from './components/AuthGuard';
import PreferencesSync from './components/PreferencesSync';
import { AuthProvider } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import { ThemeProvider } from './context/ThemeContext';
import './index.css';

const AdminPanel = lazy(() => import('./components/Admin/AdminPanel'));
const LoginForm = lazy(() => import('./components/LoginForm'));
const RegistrationPage = lazy(() => import('./pages/RegistrationPage'));
const StudentCabinetPage = lazy(() => import('./pages/StudentCabinetPage'));
const PublicationsPage = lazy(() => import('./pages/PublicationsPage'));
const UserPermissionsPage = lazy(() => import('./pages/admin/UserPermissionsPage'));

const queryClient = new QueryClient();
const routeFallback = <div className="route-fallback">Loading...</div>;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <LanguageProvider>
          <ThemeProvider>
            <QueryClientProvider client={queryClient}>
              <PreferencesSync />
              <Suspense fallback={routeFallback}>
                <Routes>
                  <Route path="/" element={<App />} />
                  <Route path="/login" element={<LoginForm />} />
                  <Route path="/register" element={<RegistrationPage />} />
                  <Route path="/publications" element={<PublicationsPage />} />
                  <Route element={<AuthGuard />}>
                    <Route path="/cabinet" element={<StudentCabinetPage />} />
                    <Route path="/dashboard" element={<Navigate to="/cabinet" replace />} />
                  </Route>
                  <Route element={<AdminGuard />}>
                    <Route path="/admin" element={<AdminPanel />} />
                    <Route path="/admin/users/:userId/permissions" element={<UserPermissionsPage />} />
                  </Route>
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
            </QueryClientProvider>
          </ThemeProvider>
        </LanguageProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
