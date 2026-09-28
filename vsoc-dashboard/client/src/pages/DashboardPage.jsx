import React from 'react';
import TopBar from '../components/layout/TopBar';
import StatsCards from '../components/dashboard/StatsCards';
import ActivityFeed from '../components/dashboard/ActivityFeed';
import Spinner from '../components/ui/Spinner';
import { useDashboardStats } from '../hooks/useDashboardStats';

const DashboardPage = ({ events }) => {
  const { stats, loading } = useDashboardStats(10000);

  return (
    <>
      <TopBar title="Dashboard" />
      <div className="page-content">
        {loading ? (
          <Spinner label="Loading dashboard..." />
        ) : (
          <>
            <StatsCards stats={stats} />
            <ActivityFeed events={events} />
          </>
        )}
      </div>
    </>
  );
};

export default DashboardPage;
