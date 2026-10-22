// Tasked: AI Enabled Task Manager - Auth Context

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { AuthState } from '../types';
import { api } from '../services/api';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string, timezone?: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem('tasked_token');
    if (!token) {
      setState({ user: null, token: null, isAuthenticated: false, isLoading: false });
      return;
    }

    api.setToken(token);
    try {
      const user = await api.getMe();
      setState({ user, token, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem('tasked_token');
      api.setToken(null);
      setState({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const tokenData = await api.login(email, password);
    localStorage.setItem('tasked_token', tokenData.access_token);
    api.setToken(tokenData.access_token);
    setState({
      user: tokenData.user,
      token: tokenData.access_token,
      isAuthenticated: true,
      isLoading: false,
    });
  };

  const register = async (email: string, password: string, displayName: string, timezone = 'UTC') => {
    const tokenData = await api.register(email, password, displayName, timezone);
    localStorage.setItem('tasked_token', tokenData.access_token);
    api.setToken(tokenData.access_token);
    setState({
      user: tokenData.user,
      token: tokenData.access_token,
      isAuthenticated: true,
      isLoading: false,
    });
  };

  const logout = () => {
    localStorage.removeItem('tasked_token');
    api.setToken(null);
    setState({ user: null, token: null, isAuthenticated: false, isLoading: false });
  };

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}