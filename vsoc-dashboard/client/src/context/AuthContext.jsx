import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

// Safely decode a JWT payload without any external library
const decodeJwt = (token) => {
  try {
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    return decoded;
  } catch {
    return null;
  }
};

// Returns true if the token is present and not yet expired
const isTokenValid = (token) => {
  if (!token) return false;
  const decoded = decodeJwt(token);
  if (!decoded || !decoded.exp) return false;
  // exp is in seconds; Date.now() is in milliseconds
  return decoded.exp * 1000 > Date.now();
};

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8081/api';

export const AuthProvider = ({ children }) => {
  // On initial load, discard any expired token immediately
  const [token, setToken] = useState(() => {
    const t = localStorage.getItem('fleet_token');
    if (!isTokenValid(t)) {
      localStorage.removeItem('fleet_token');
      return null;
    }
    return t;
  });
  const [user, setUser] = useState(() => {
    const t = localStorage.getItem('fleet_token');
    return isTokenValid(t) ? decodeJwt(t) : null;
  });

  useEffect(() => {
    if (token) {
      localStorage.setItem('fleet_token', token);
      setUser(decodeJwt(token));
    } else {
      localStorage.removeItem('fleet_token');
      setUser(null);
    }
  }, [token]);

  const login = async (username, password) => {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        // Surface the real error from the server if possible
        let msg = 'Invalid credentials';
        try {
          const body = await response.json();
          msg = body.message || body.error || msg;
        } catch { /* not JSON */ }
        throw new Error(msg);
      }

      const data = await response.json();
      setToken(data.token);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const logout = () => setToken(null);

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
