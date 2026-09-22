import React, { useState } from 'react';
import { Plus, Server, Activity, ShieldAlert } from 'lucide-react';
import VehicleCard from './VehicleCard';

const FleetDashboard = ({ fleet, loading, onAddVehicle, onRemoveVehicle }) => {
  const [newVehicleId, setNewVehicleId] = useState('');
  
  const handleAdd = (e) => {
    e.preventDefault();
    if (!newVehicleId.trim()) return;
    onAddVehicle(newVehicleId.trim());
    setNewVehicleId('');
  };

  const healthyCount = fleet.filter(v => v.status === 'Healthy').length;
  const compromisedCount = fleet.length - healthyCount;

  return (
    <div className="dashboard-container">
      {/* Top Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon blue"><Server size={24} /></div>
          <div className="metric-info">
            <h3>Total Vehicles</h3>
            <p>{fleet.length}</p>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon green"><Activity size={24} /></div>
          <div className="metric-info">
            <h3>Healthy Nodes</h3>
            <p>{healthyCount}</p>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon red"><ShieldAlert size={24} /></div>
          <div className="metric-info">
            <h3>Threatened</h3>
            <p>{compromisedCount}</p>
          </div>
        </div>
      </div>

      {/* Fleet Controls */}
      <div className="fleet-controls">
        <h2>Active Fleet</h2>
        <form onSubmit={handleAdd} className="add-vehicle-form">
          <input 
            type="text" 
            placeholder="Enter Vehicle ID (e.g. 42)" 
            value={newVehicleId}
            onChange={(e) => setNewVehicleId(e.target.value)}
            className="input-field"
          />
          <button type="submit" className="btn-primary">
            <Plus size={18} />
            <span>Add Vehicle</span>
          </button>
        </form>
      </div>

      {/* Vehicle Grid */}
      <div className="vehicle-grid">
        {loading && fleet.length === 0 ? (
          <div className="loading-state">Loading fleet data...</div>
        ) : fleet.length === 0 ? (
          <div className="empty-state">No vehicles in the fleet. Add one to begin tracking.</div>
        ) : (
          fleet.map(vehicle => (
            <VehicleCard 
              key={vehicle.id} 
              vehicle={vehicle} 
              onRemove={() => onRemoveVehicle(vehicle.id)} 
            />
          ))
        )}
      </div>
    </div>
  );
};

export default FleetDashboard;
