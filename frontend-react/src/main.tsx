import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import AuthGuard from './components/AuthGuard';
import LoginForm from './components/LoginForm';
import RegistrationPage from './pages/RegistrationPage';
import App from './App';

const queryClient = new QueryClient();

// Компонент-обертка для управления редиректами
// ... (убран unused ProtectedRedirect)

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

  return (
    <BrowserRouter>
      <Routes>
        {/* Публичные маршруты */}
        <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginForm />} />
        <Route path="/autch" element={user ? <Navigate to="/dashboard" replace /> : <LoginForm />} />
        <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <RegistrationPage />} />

        {/* Маршрут по умолчанию */}
        <Route path="/" element={
          user
            ? <Navigate to="/dashboard" replace />
            : <Navigate to="/autch" replace />
        } />

        {/* Защищенные маршруты */}
        <Route element={<AuthGuard />}>
          <Route path="/dashboard" element={<App />} />
          <Route path="/dashboard/" element={<App />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/admin/" element={<AdminPanel />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

function AdminPanel() {
  const { user } = useAuth();
  const { t } = useLanguage();

  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="p-10 text-white bg-[#0a0a0b] min-h-screen font-sans">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-black tracking-tighter mb-4 italic text-blue-500">{t.adminTitle}</h1>
        <div className="h-0.5 w-full bg-zinc-800 mb-8"></div>
        <p className="text-zinc-400 font-bold uppercase tracking-widest text-sm">{t.adminOperator}: {user?.email}</p>
        <div className="mt-12 p-8 border border-zinc-800 rounded-3xl bg-zinc-900/50 backdrop-blur-md">
          <p className="text-zinc-500 font-medium">{t.adminReady}</p>
        </div>
      </div>
    </div>
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
