import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ToastProvider } from './context/ToastContext';
import { useFleet } from './hooks/useFleet';
import Layout from './components/layout/Layout';
import DashboardPage from './pages/DashboardPage';
import FleetPage from './pages/FleetPage';
import './index.css';

function AppContent() {
  const { vehicles, loading, error, connected, events, refetch } = useFleet();

  return (
    <Routes>
      <Route element={<Layout connected={connected} />}>
        <Route index element={<DashboardPage events={events} />} />
        <Route path="fleet" element={
          <FleetPage vehicles={vehicles} loading={loading} onRefresh={refetch} />
        } />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </BrowserRouter>
  );
}

export default App;
