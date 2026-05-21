import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { isAdminUser } from '../security/adminAccess';

export default function AdminGuard() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return isAdminUser(user) ? <Outlet /> : <Navigate to="/dashboard" replace />;
}
