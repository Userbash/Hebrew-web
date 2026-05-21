import 'bootstrap/dist/css/bootstrap.min.css';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import App from './App';
import AdminPanel from './components/Admin/AdminPanel';
import AdminGuard from './components/AdminGuard';
import AuthGuard from './components/AuthGuard';
import LoginForm from './components/LoginForm';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import { ThemeProvider } from './context/ThemeContext';
import RegistrationPage from './pages/RegistrationPage';
import { getDefaultRouteForUser, isAdminUser } from './security/adminAccess';

const queryClient = new QueryClient();

function DashboardEntry() {
  const { user } = useAuth();

  if (isAdminUser(user)) {
    return <Navigate to="/admin" replace />;
  }

  return <App />;
}

function Router() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex flex-col items-center justify-center text-white font-sans">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
        <div className="text-[10px] font-black tracking-[0.5em] uppercase opacity-50 text-blue-500">
          Initializing 3X-UI Secure Bridge
        </div>
      </div>
    );
  }

  const homeRoute = getDefaultRouteForUser(user);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={user ? <Navigate to={homeRoute} replace /> : <LoginForm />} />
        <Route path="/register" element={user ? <Navigate to={homeRoute} replace /> : <RegistrationPage />} />
        <Route path="/autch" element={<Navigate to="/login" replace />} />
        <Route path="/" element={<Navigate to={homeRoute} replace />} />

        <Route element={<AuthGuard />}>
          <Route path="/dashboard" element={<DashboardEntry />} />
          <Route path="/dashboard/" element={<DashboardEntry />} />

          <Route element={<AdminGuard />}>
            <Route path="/admin" element={<AdminPanel />} />
            <Route path="/admin/" element={<AdminPanel />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default function Root() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <LanguageProvider>
          <AuthProvider>
            <Router />
          </AuthProvider>
        </LanguageProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
