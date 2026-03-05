"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { User } from "@/lib/auth-api";
import * as authApi from "@/lib/auth-api";

const TOKEN_KEY = "archangel_auth_token";

type AuthState = {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
};

type AuthContextValue = AuthState & {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() =>
    typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const applyToken = useCallback((newToken: string | null) => {
    if (typeof window === "undefined") return;
    if (newToken) {
      localStorage.setItem(TOKEN_KEY, newToken);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
    setToken(newToken);
  }, []);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    authApi.getMe(token).then((u) => {
      if (!cancelled) {
        setUser(u);
      }
      if (!cancelled) setLoading(false);
    }).catch(() => {
      if (!cancelled) {
        applyToken(null);
        setUser(null);
      }
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [token, applyToken]);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    try {
      const data = await authApi.login(email, password);
      applyToken(data.access_token);
      setUser(data.user);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed");
      throw e;
    }
  }, [applyToken]);

  const register = useCallback(
    async (email: string, password: string, name?: string) => {
      setError(null);
      try {
        const data = await authApi.register(email, password, name);
        applyToken(data.access_token);
        setUser(data.user);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Registration failed");
        throw e;
      }
    },
    [applyToken]
  );

  const logout = useCallback(() => {
    applyToken(null);
    setUser(null);
    setError(null);
  }, [applyToken]);

  const clearError = useCallback(() => setError(null), []);

  const value: AuthContextValue = {
    user,
    token,
    loading,
    error,
    login,
    register,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
