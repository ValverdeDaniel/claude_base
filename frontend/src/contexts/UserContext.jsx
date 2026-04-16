import { createContext, useContext, useState, useEffect } from 'react';
import * as api from '../services/api';

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!user;

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      refreshProfile().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function refreshProfile() {
    try {
      const response = await api.getProfile();
      setUser(response.data);
    } catch {
      localStorage.removeItem('token');
      setUser(null);
    }
  }

  async function login(username, password) {
    const response = await api.login(username, password);
    localStorage.setItem('token', response.data.token);
    setUser(response.data.user);
    return response.data;
  }

  async function signup(username, email, password) {
    const response = await api.signup(username, email, password);
    localStorage.setItem('token', response.data.token);
    setUser(response.data.user);
    return response.data;
  }

  async function logout() {
    try {
      await api.logout();
    } catch {
      // Token may already be invalid, continue with local cleanup
    }
    localStorage.removeItem('token');
    setUser(null);
  }

  return (
    <UserContext.Provider
      value={{ user, loading, isAuthenticated, login, signup, logout, refreshProfile }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
