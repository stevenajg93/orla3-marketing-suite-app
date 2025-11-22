'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, ApiError } from '@/lib/api-client';

interface User {
  id: string;
  name: string;
  email: string;
  organization_name?: string;
  organization_slug?: string;
  role: string;
  plan: string;
  email_verified: boolean;
  is_super_admin?: boolean;
  profile_image_url?: string;
  timezone?: string;
  created_at?: string;
  last_login_at?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, organizationName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check authentication state on mount via HttpOnly cookie
  // The cookie is sent automatically with credentials: 'include'
  useEffect(() => {
    const initAuth = async () => {
      try {
        // This request will include the HttpOnly cookie automatically
        const response = await api.get('/auth/me');
        if (response.success) {
          setUser(response.user);
        }
      } catch (error) {
        // No valid session - user is not logged in
        // HttpOnly cookies are managed by the backend
        console.debug('No active session');
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      // Login sets HttpOnly cookies via Set-Cookie headers
      const response = await api.post('/auth/login', { email, password });

      if (response.success) {
        // HttpOnly cookies are automatically set by the backend
        // Set user state from response
        setUser(response.user);
      } else {
        throw new Error(response.detail || 'Login failed');
      }
    } catch (error: any) {
      console.error('Login error:', error);
      // Re-throw ApiError to preserve status code for 402 handling
      if (error instanceof ApiError) {
        throw error;
      }
      throw new Error(error.message || 'Login failed');
    }
  };

  const register = async (
    name: string,
    email: string,
    password: string,
    organizationName?: string
  ) => {
    try {
      const response = await api.post('/auth/register', {
        name,
        email,
        password,
        organization_name: organizationName,
      });

      if (response.success) {
        // Auto-login after registration
        await login(email, password);
      } else {
        throw new Error(response.detail || 'Registration failed');
      }
    } catch (error: any) {
      console.error('Registration error:', error);
      throw new Error(error.response?.data?.detail || error.message || 'Registration failed');
    }
  };

  const logout = async () => {
    try {
      // Logout clears HttpOnly cookies via Set-Cookie headers
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear user state - cookies are cleared by the backend
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const response = await api.get('/auth/me');
      if (response.success) {
        setUser(response.user);
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
