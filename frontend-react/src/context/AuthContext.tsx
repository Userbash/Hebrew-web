import { createContext, useContext, useEffect, useState, type Dispatch, type SetStateAction } from 'react';
import api from '../api/client';

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
}

interface AuthContextValue {
  user: User | null;
  setUser: Dispatch<SetStateAction<User | null>>;
  isLoading: boolean;
  setIsLoading: Dispatch<SetStateAction<boolean>>;
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
      } catch (_meError) {
        // Access token may be expired: try refresh once.
      }

      try {
        await api.post('/auth/refresh');
        const meAfterRefresh = await api.get('/auth/me');
        if (isMounted) {
          setUser(isUserPayload(meAfterRefresh.data) ? meAfterRefresh.data : null);
        }
      } catch (_refreshError) {
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

  return (
    <AuthContext.Provider value={{ user, setUser, isLoading, setIsLoading }}>
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
