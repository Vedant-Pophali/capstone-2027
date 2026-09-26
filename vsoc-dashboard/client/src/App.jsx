import React, { useState, useEffect } from 'react';
import { apiService } from './services/api';
import FleetDashboard from './components/FleetDashboard';
import { io } from 'socket.io-client';
import './index.css';

const SOCKET_URL = 'http://localhost:3001';

function App() {
  const [fleet, setFleet] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchFleet = async () => {
    try {
      setLoading(true);
      const data = await apiService.fetchFleet();
      setFleet(data);
      setError(null);
    } catch (err) {
      setError('Failed to load fleet data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchFleet();

    // Setup WebSocket connection for real-time, event-driven updates
    const socket = io(SOCKET_URL);

    socket.on('connect', () => {
      console.log('Connected to VSOC WebSocket server');
    });

    socket.on('fleet_update', (event) => {
      console.log('Received real-time update:', event);
      
      setFleet(currentFleet => {
        switch (event.type) {
          case 'ADDED':
            // Add new vehicle if it doesn't already exist in state
            if (!currentFleet.find(v => v.id === event.vehicle.id)) {
              return [...currentFleet, event.vehicle];
            }
            return currentFleet;
            
          case 'REMOVED':
            return currentFleet.filter(v => v.id !== event.vehicleId);
            
          case 'STATUS_CHANGED':
            return currentFleet.map(v => 
              v.id === event.vehicle.id ? event.vehicle : v
            );
            
          default:
            return currentFleet;
        }
      });
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from VSOC WebSocket server');
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const handleAddVehicle = async (vehicleData) => {
    try {
      await apiService.addVehicle(vehicleData);
      await fetchFleet();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleRemoveVehicle = async (vehicleId) => {
    try {
      await apiService.removeVehicle(vehicleId);
      await fetchFleet();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>VSOC Admin Dashboard</h1>
        <p>Real-time vehicle fleet monitoring and health tracking</p>
      </header>
      
      <main className="app-main">
        {error && <div className="error-banner">{error}</div>}
        <FleetDashboard 
          fleet={fleet} 
          loading={loading} 
          onAddVehicle={handleAddVehicle} 
          onRemoveVehicle={handleRemoveVehicle} 
        />
      </main>
    </div>
  );
}

export default App;
