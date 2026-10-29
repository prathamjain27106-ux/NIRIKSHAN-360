/* =================================================================
   Auth Context — JWT authentication state management
   ================================================================= */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { User } from '../types';
import { authApi, getStoredTokens, clearTokens } from '../api/client';

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  isDemoMode: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

// Demo user for when backend auth is not available
const DEMO_USER: User = {
  id: 1, username: 'admin', email: 'admin@nirikshan.demo',
  first_name: 'System', last_name: 'Admin', role: 'ADMIN',
  cell: '', is_active: true, created_at: new Date().toISOString(),
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDemoMode, setIsDemoMode] = useState(false);

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      const tokens = getStoredTokens();
      if (tokens) {
        try {
          const me = await authApi.me();
          setUser(me);
        } catch {
          // Token expired or backend down — check if demo mode
          const demoFlag = localStorage.getItem('nirikshan_demo');
          if (demoFlag) {
            setUser(DEMO_USER);
            setIsDemoMode(true);
          } else {
            clearTokens();
          }
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setError(null);
    setLoading(true);
    try {
      await authApi.login(username, password);
      const me = await authApi.me();
      setUser(me);
      setIsDemoMode(false);
      localStorage.removeItem('nirikshan_demo');
    } catch {
      // Backend auth failed — try demo mode
      const { demoAccounts } = await import('../data/demo');
      const demoAccount = demoAccounts.find(a => a.username === username && a.password === password);
      if (demoAccount) {
        const demoUser: User = {
          ...DEMO_USER,
          username: demoAccount.username,
          role: demoAccount.role as User['role'],
          cell: demoAccount.cell as User['cell'],
          first_name: demoAccount.role === 'ADMIN' ? 'System' : demoAccount.username,
          last_name: demoAccount.role === 'ADMIN' ? 'Admin' : '',
        };
        setUser(demoUser);
        setIsDemoMode(true);
        localStorage.setItem('nirikshan_demo', '1');
        // Store fake tokens for demo mode
        localStorage.setItem('nirikshan_access', 'demo-token');
        localStorage.setItem('nirikshan_refresh', 'demo-refresh');
      } else {
        setError('Invalid credentials. Check the demo accounts panel for valid logins.');
        throw new Error('Invalid credentials');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    authApi.logout();
    localStorage.removeItem('nirikshan_demo');
    setUser(null);
    setIsDemoMode(false);
  }, []);

  return (
    <AuthContext.Provider value={{
      user, loading, error, isDemoMode,
      isAuthenticated: !!user,
      login, logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
