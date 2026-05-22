import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import UiPreferencesControls from '../../components/Layout/UiPreferencesControls';
import AccessDenied from '../../components/AccessDenied';
import { adminUsersApi, type AdminUser } from '../../api/adminUsers';
import { useAuth } from '../../context/AuthContext';
import { canEditUserPermissions } from '../../security/canEditUserPermissions';

interface UserPermissionsState {
  roles: string[];
  permissions: string[];
  availableRoles: string[];
  availablePermissions: string[];
}

export default function UserPermissionsPage() {
  const { userId = '' } = useParams();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();

  const [targetUser, setTargetUser] = useState<AdminUser | null>(null);
  const [state, setState] = useState<UserPermissionsState>({
    roles: [],
    permissions: [],
    availableRoles: [],
    availablePermissions: [],
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await adminUsersApi.getUserPermissions(userId);
        setTargetUser(data.user);
        setState({
          roles: data.roles,
          permissions: data.permissions,
          availableRoles: data.availableRoles,
          availablePermissions: data.availablePermissions,
        });
      } catch (e) {
        const apiMessage = (e as { response?: { data?: { message?: string } } })?.response?.data?.message;
        setError(apiMessage || 'Failed to load user permissions');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      void load();
    }
  }, [userId]);

  const editable = useMemo(() => canEditUserPermissions(currentUser, targetUser), [currentUser, targetUser]);

  const toggleRole = (roleKey: string) => {
    setState((prev) => ({
      ...prev,
      roles: prev.roles.includes(roleKey)
        ? prev.roles.filter((item) => item !== roleKey)
        : [...prev.roles, roleKey],
    }));
  };

  const handleSave = async () => {
    if (!targetUser) return;
    setSaving(true);
    setError('');
    try {
      await adminUsersApi.updateUserPermissions(targetUser.id, {
        roles: state.roles,
        permissions: state.permissions,
      });
      navigate('/admin');
    } catch (e) {
      const apiMessage = (e as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(apiMessage || 'Failed to update permissions');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="site-page"><div className="site-wrap">
        <UiPreferencesControls className="site-prefs" /><div className="site-muted">Loading...</div></div></div>;
  }

  if (error && !targetUser) {
    return <div className="site-page"><div className="site-wrap"><div className="site-error">{error}</div></div></div>;
  }

  if (!editable) {
    return <AccessDenied message="У вас нет прав изменять права этого пользователя" />;
  }

  return (
    <main className="site-page">
      <div className="site-wrap">
        <section className="site-section-head">
          <p className="site-kicker">Access & Governance</p>
          <h1>Управление правами пользователя</h1>
          <p>
            Изменения будет видно в audit trail. Актор: <strong>{currentUser?.email || currentUser?.id}</strong>,
            цель: <strong>{targetUser?.email || targetUser?.id}</strong>.
          </p>
        </section>

        {error && <div className="site-error">{error}</div>}

        <section className="site-card">
          <h3>Roles</h3>
          <div className="site-role-grid">
            {state.availableRoles.map((role) => (
              <label key={role} className="site-checkbox">
                <input
                  type="checkbox"
                  checked={state.roles.includes(role)}
                  onChange={() => toggleRole(role)}
                />
                <span>{role}</span>
              </label>
            ))}
          </div>
        </section>

        <section className="site-card mt-3">
          <h3>Effective permissions</h3>
          <div className="d-flex flex-wrap gap-2">
            {state.permissions.map((permission) => (
              <code key={permission} className="site-code">{permission}</code>
            ))}
          </div>
        </section>

        <section className="site-box mt-3">
          <div className="site-muted mt-0">
            Audit warning: вы изменяете роли и effective permissions. Действие будет записано в журнал.
          </div>
        </section>

        <div className="site-cta-row">
          <button className="site-btn site-btn-primary" disabled={saving} onClick={() => void handleSave()}>
            {saving ? 'Saving...' : 'Save'}
          </button>
          <Link to="/admin" className="site-btn site-btn-secondary">Cancel</Link>
        </div>
      </div>
    </main>
  );
}
