import React from 'react';
import { Car, Trash2, Cpu, Clock } from 'lucide-react';

const VehicleCard = ({ vehicle, onRemove }) => {
  const isHealthy = vehicle.status === 'Healthy';
  
  // Format the date
  const addedDate = new Date(vehicle.addedAt).toLocaleTimeString();
  
  // Format container ID (first 12 chars)
  const shortContainerId = vehicle.containerId ? vehicle.containerId.substring(0, 12) : 'N/A';

  return (
    <div className={`vehicle-card ${isHealthy ? 'healthy' : 'threatened'}`}>
      <div className="card-header">
        <div className="vehicle-id">
          <Car size={20} />
          <span>Vehicle {vehicle.id}</span>
        </div>
        <div className={`status-badge ${isHealthy ? 'bg-green' : 'bg-red'}`}>
          {vehicle.status}
        </div>
      </div>
      
      <div className="card-body">
        {vehicle.owner && (
          <div className="info-row">
            <span className="text-muted">Owner:</span>
            <span className="value font-mono">{vehicle.owner}</span>
          </div>
        )}
        {vehicle.model && (
          <div className="info-row">
            <span className="text-muted">Model:</span>
            <span className="value font-mono">{vehicle.model}</span>
          </div>
        )}
        <div className="info-row">
          <Cpu size={16} className="text-muted" />
          <span className="text-muted">Container:</span>
          <span className="value font-mono">{shortContainerId}</span>
        </div>
        <div className="info-row">
          <Clock size={16} className="text-muted" />
          <span className="text-muted">Added:</span>
          <span className="value">{addedDate}</span>
        </div>
      </div>
      
      <div className="card-footer">
        <button onClick={onRemove} className="btn-danger" title="Remove Vehicle">
          <Trash2 size={16} />
          <span>Remove</span>
        </button>
      </div>
    </div>
  );
};

export default VehicleCard;
