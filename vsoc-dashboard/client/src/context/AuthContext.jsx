import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('fleet_token'));
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (token) {
      localStorage.setItem('fleet_token', token);
      // Optional: If there's an endpoint to get current user details, fetch it here.
      // For now, we'll just parse the JWT if needed, or assume logged in.
    } else {
      localStorage.removeItem('fleet_token');
      setUser(null);
    }
  }, [token]);

  const login = async (username, password) => {
    try {
      // Use standard fetch here because api.js might rely on token which we don't have yet,
      // or we can use api.js if it doesn't strictly require a token for /auth/login.
      // SecurityConfig permits /api/auth/** without token.
      const response = await fetch(import.meta.env.VITE_API_BASE + '/auth/login' || 'http://localhost:8081/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();
      setToken(data.token);
      // Could set user details here if returned (e.g. data.role)
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
