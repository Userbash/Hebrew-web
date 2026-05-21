import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AuthGuard() {
  const { user, loading } = useAuth();

  if (loading) return <div>Загрузка...</div>;
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}
