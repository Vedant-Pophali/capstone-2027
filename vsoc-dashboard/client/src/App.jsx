import React, { useState, useEffect } from 'react';
import { apiService } from './services/api';
import FleetDashboard from './components/FleetDashboard';
import './index.css';

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
    fetchFleet();
    // In a real application, you might use WebSockets or polling here.
    const interval = setInterval(fetchFleet, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAddVehicle = async (vehicleId) => {
    try {
      await apiService.addVehicle(vehicleId);
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
