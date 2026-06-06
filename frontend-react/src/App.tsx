import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import { ThemeProvider } from './context/ThemeContext';
import AuthGuard from './components/AuthGuard';
import AdminGuard from './components/AdminGuard';
import PreferencesSync from './components/PreferencesSync';
import LoginForm from './components/LoginForm';
import PublicHomePage from './pages/PublicHomePage';
import PublicationsPage from './pages/PublicationsPage';
import RegistrationPage from './pages/RegistrationPage';
import OrchestratorChatPage from './pages/OrchestratorChatPage';
import AdminPanel from './components/Admin/AdminPanel';
import DevToolkitPage from './pages/admin/DevToolkitPage';
import { AdminLayout } from './components/Admin/AdminLayout';

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ThemeProvider>
            <LanguageProvider>
              <PreferencesSync />
              <Routes>
                <Route path="/" element={<PublicHomePage />} />
                <Route path="/login" element={<LoginForm />} />
                <Route path="/register" element={<RegistrationPage />} />
                <Route path="/publications" element={<PublicationsPage />} />
                <Route path="/orchestrator-chat" element={<OrchestratorChatPage />} />
                <Route element={<AuthGuard />}>
                  <Route path="/cabinet" element={<div>Cabinet</div>} />
                </Route>
                <Route element={<AdminGuard />}>
                  <Route path="/admin" element={<AdminLayout><AdminPanel /></AdminLayout>} />
                  <Route path="/admin/dev-toolkit" element={<AdminLayout><DevToolkitPage /></AdminLayout>} />
                </Route>
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </LanguageProvider>
          </ThemeProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
