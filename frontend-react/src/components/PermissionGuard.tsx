import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { hasPermission, type PermissionAction, type PermissionScope } from '../security/rbac';

interface PermissionGuardProps {
  resource?: string;
  action?: PermissionAction;
  scope?: PermissionScope;
  permission?: string;
  fallbackTo?: string;
}

export default function PermissionGuard({ resource, action, scope, permission, fallbackTo = '/cabinet' }: PermissionGuardProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const allowed = permission
    ? hasPermission(user, permission)
    : (resource && action ? hasPermission(user, { resource, action, scope }) : false);

  if (!allowed) {
    return <Navigate to={fallbackTo} replace />;
  }

  return <Outlet />;
}
