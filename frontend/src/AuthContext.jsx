import React, { createContext, useContext, useState, useEffect } from 'react';
import { clearTokens } from './api/client';

const AuthContext = createContext();

function getInitialAuthState() {
  return !!localStorage.getItem('access');
}

export function AuthProvider({ children }) {
  const [isLoggedIn, setIsLoggedIn] = useState(getInitialAuthState);

  const logout = () => {
    clearTokens();
    setIsLoggedIn(false);
  };

  const login = () => setIsLoggedIn(true);

  useEffect(() => {
    const handleAuthLogout = () => setIsLoggedIn(false);
    window.addEventListener('auth:logout', handleAuthLogout);
    return () => window.removeEventListener('auth:logout', handleAuthLogout);
  }, []);

  return (
    <AuthContext.Provider value={{ isLoggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
