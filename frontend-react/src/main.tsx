import 'bootstrap/dist/css/bootstrap.min.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import App from './App';
import AdminGuard from './components/AdminGuard';
import AuthGuard from './components/AuthGuard';
import PermissionGuard from './components/PermissionGuard';
import LoginForm from './components/LoginForm';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import PreferencesSync from './components/PreferencesSync';
import { ThemeProvider } from './context/ThemeContext';
import { getDefaultRouteForUser, isAdminUser } from './security/adminAccess';
import './index.css';

const AdminPanel = lazy(() => import('./components/Admin/AdminPanel'));
const RegistrationPage = lazy(() => import('./pages/RegistrationPage'));
const PublicHomePage = lazy(() => import('./pages/PublicHomePage'));
const PublicationsPage = lazy(() => import('./pages/PublicationsPage'));
const UserPermissionsPage = lazy(() => import('./pages/admin/UserPermissionsPage'));

const queryClient = new QueryClient();

function CabinetEntry() {
  const { user } = useAuth();

  if (isAdminUser(user)) {
    return <Navigate to="/admin" replace />;
  }

  return <App />;
}

function RouteFallback() {
  return <div className="site-wrap"><div className="site-muted">Loading...</div></div>;
}

function Router() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div className="site-wrap"><div className="site-muted">Initializing...</div></div>;
  }

  const homeRoute = getDefaultRouteForUser(user);

  return (
    <BrowserRouter>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<PublicHomePage />} />
          <Route path="/publications" element={<PublicationsPage />} />

          <Route path="/login" element={user ? <Navigate to={homeRoute} replace /> : <LoginForm />} />
          <Route path="/register" element={user ? <Navigate to={homeRoute} replace /> : <RegistrationPage />} />
          <Route path="/autch" element={<Navigate to="/login" replace />} />

          <Route element={<AuthGuard />}>
            <Route path="/cabinet" element={<CabinetEntry />} />
            <Route path="/dashboard" element={<Navigate to="/cabinet" replace />} />

            <Route element={<PermissionGuard resource="publications" action="read" scope="any" fallbackTo="/cabinet" />}>
              <Route path="/moderation" element={<Navigate to="/admin" replace />} />
            </Route>
            <Route element={<PermissionGuard permission="users.permissions.manage" fallbackTo="/cabinet" />}>
              <Route path="/admin/users/:userId/permissions" element={<UserPermissionsPage />} />
            </Route>

            <Route element={<AdminGuard />}>
              <Route path="/admin" element={<AdminPanel />} />
              <Route path="/admin/" element={<AdminPanel />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default function Root() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <PreferencesSync />
        <ThemeProvider>
          <LanguageProvider>
            <Router />
          </LanguageProvider>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
