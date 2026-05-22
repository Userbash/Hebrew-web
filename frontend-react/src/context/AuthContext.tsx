import { createContext, useContext, useEffect, useState, type Dispatch, type SetStateAction } from 'react';
import api from '../api/client';

export type RoleKey =
  | 'root'
  | 'platform_admin'
  | 'security_admin'
  | 'content_admin'
  | 'editor'
  | 'moderator'
  | 'support'
  | 'analyst'
  | 'user'
  | (string & {});

export interface AccessProfile {
  roleKeys: RoleKey[];
  highestRole: RoleKey;
  highestPriority: number;
  isSystemBlocked: boolean;
}

export interface UserUiPreferences {
  language?: 'ru' | 'en' | 'he';
  languageMode?: 'system' | 'ru' | 'en' | 'he';
  themeMode?: 'system' | 'light' | 'dark';
  timezone?: string;
  density?: 'compact' | 'comfortable';
  reduceMotion?: boolean;
  adminLandingSection?: string;
  dashboardLayout?: 'classic' | 'focus';
}

export interface User {
  id: string;
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  role?: string;
  xp_total?: number;
  level?: number;
  created_at?: string;
  updated_at?: string;
  registered_at?: string;
  last_login?: string;
  access?: AccessProfile | null;
  ui_preferences?: UserUiPreferences;
}

interface AuthContextValue {
  user: User | null;
  setUser: Dispatch<SetStateAction<User | null>>;
  isLoading: boolean;
  setIsLoading: Dispatch<SetStateAction<boolean>>;
  hasRole: (role: RoleKey) => boolean;
  hasAnyRole: (roles: RoleKey[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const isUserPayload = (payload: unknown): payload is User => {
  return Boolean(
    payload &&
    typeof payload === 'object' &&
    'id' in payload &&
    typeof (payload as { id?: unknown }).id === 'string'
  );
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const bootstrapAuth = async () => {
      try {
        const me = await api.get('/auth/me');
        if (isMounted) {
          setUser(isUserPayload(me.data) ? me.data : null);
          setIsLoading(false);
        }
        return;
      } catch {
        // Access token may be expired: try refresh once.
      }

      try {
        await api.post('/auth/refresh');
        const meAfterRefresh = await api.get('/auth/me');
        if (isMounted) {
          setUser(isUserPayload(meAfterRefresh.data) ? meAfterRefresh.data : null);
        }
      } catch {
        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    bootstrapAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const hasRole = (role: RoleKey) => {
    if (!user?.access?.roleKeys) {
      return false;
    }

    return user.access.roleKeys.includes(role);
  };

  const hasAnyRole = (roles: RoleKey[]) => {
    if (!user?.access?.roleKeys || roles.length === 0) {
      return false;
    }

    return roles.some((role) => user.access?.roleKeys.includes(role));
  };

  return (
    <AuthContext.Provider value={{ user, setUser, isLoading, setIsLoading, hasRole, hasAnyRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
