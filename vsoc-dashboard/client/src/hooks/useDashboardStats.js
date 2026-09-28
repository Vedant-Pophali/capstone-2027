import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

/**
 * Custom hook for dashboard statistics.
 * Polls the /api/dashboard/stats endpoint at a configurable interval.
 */
export function useDashboardStats(pollInterval = 15000) {
  const [stats, setStats] = useState({
    totalVehicles: 0,
    healthyVehicles: 0,
    compromisedVehicles: 0,
    containersRunning: 0,
  });
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    try {
      const data = await apiService.fetchDashboardStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, pollInterval);
    return () => clearInterval(interval);
  }, [fetchStats, pollInterval]);

  return { stats, loading, refetch: fetchStats };
}
