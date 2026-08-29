/* Authentication context providing user state and auth methods */

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { authService } from '../services/auth';
import type { AuthResponse } from '../types';

interface AuthUser {
  user_id: string;
  role: 'employee' | 'agent';
  name: string;
}

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, role: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

function saveAuth(data: AuthResponse) {
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem(
    'user',
    JSON.stringify({
      user_id: data.user_id,
      role: data.role,
      name: data.name,
    })
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('user');
    const token = localStorage.getItem('access_token');
    if (stored && token) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await authService.login(email, password);
    const authUser: AuthUser = { user_id: data.user_id, role: data.role, name: data.name };
    saveAuth(data);
    setUser(authUser);
  }, []);

  const register = useCallback(
    async (name: string, email: string, password: string, role: string) => {
      const data = await authService.register(name, email, password, role);
      const authUser: AuthUser = { user_id: data.user_id, role: data.role, name: data.name };
      saveAuth(data);
      setUser(authUser);
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
