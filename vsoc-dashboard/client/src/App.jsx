import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ToastProvider } from './context/ToastContext';
import { AuthProvider } from './context/AuthContext';
import { useFleet } from './hooks/useFleet';
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import FleetPage from './pages/FleetPage';
import './index.css';

function AppContent() {
  const { vehicles, loading, error, connected, events, refetch } = useFleet();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout connected={connected} />}>
          <Route index element={<DashboardPage events={events} />} />
          <Route path="fleet" element={
            <FleetPage vehicles={vehicles} loading={loading} onRefresh={refetch} />
          } />
        </Route>
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <AppContent />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
