import React from 'react';
import { Server, Activity, ShieldAlert, Container } from 'lucide-react';

const StatsCards = ({ stats }) => {
  const cards = [
    { label: 'Total Vehicles', value: stats.totalVehicles, icon: Server, color: 'emerald' },
    { label: 'Healthy Nodes', value: stats.healthyVehicles, icon: Activity, color: 'green' },
    { label: 'Compromised', value: stats.compromisedVehicles, icon: ShieldAlert, color: 'red' },
    { label: 'Containers Running', value: stats.containersRunning, icon: Container, color: 'amber' },
  ];

  return (
    <div className="stats-grid">
      {cards.map(card => {
        const Icon = card.icon;
        return (
          <div className="stat-card" key={card.label}>
            <div className={`stat-icon ${card.color}`}>
              <Icon size={20} />
            </div>
            <div>
              <div className="stat-label">{card.label}</div>
              <div className="stat-value">{card.value}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StatsCards;
