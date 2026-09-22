const { exec } = require('child_process');

class FleetService {
  constructor() {
    this.vehicles = new Map(); // Store simulated vehicles and their container IDs
  }

  // Get all active vehicles and their health status
  async getFleetStatus() {
    // Return the mocked state but could be extended to query actual docker containers
    const fleet = [];
    for (const [id, vehicle] of this.vehicles.entries()) {
      fleet.push({
        id,
        status: vehicle.status,
        containerId: vehicle.containerId,
        addedAt: vehicle.addedAt
      });
    }
    return fleet;
  }

  // Add a new vehicle and spin up a container
  async addVehicle(vehicleId) {
    if (this.vehicles.has(vehicleId)) {
      throw new Error(`Vehicle ${vehicleId} already exists`);
    }

    // Command to run a docker container. 
    // Using a lightweight alpine image that just sleeps, acting as a dummy for the edge-vehicle
    const cmd = `docker run -d --name vehicle_${vehicleId} -e VEHICLE_ID=${vehicleId} alpine sleep infinity`;
    
    return new Promise((resolve, reject) => {
      exec(cmd, (error, stdout, stderr) => {
        if (error) {
          console.error(`Error starting container: ${error.message}`);
          reject(error);
          return;
        }
        
        const containerId = stdout.trim();
        this.vehicles.set(vehicleId, {
          status: 'Healthy', // Mock initial status
          containerId: containerId,
          addedAt: new Date().toISOString()
        });
        
        resolve(this.vehicles.get(vehicleId));
      });
    });
  }

  // Remove a vehicle and stop/remove its container
  async removeVehicle(vehicleId) {
    const vehicle = this.vehicles.get(vehicleId);
    if (!vehicle) {
      throw new Error(`Vehicle ${vehicleId} not found`);
    }

    const cmd = `docker rm -f vehicle_${vehicleId}`;
    
    return new Promise((resolve, reject) => {
      exec(cmd, (error, stdout, stderr) => {
        if (error) {
          console.error(`Error stopping container: ${error.message}`);
          reject(error);
          return;
        }
        
        this.vehicles.delete(vehicleId);
        resolve({ success: true, vehicleId });
      });
    });
  }
}

module.exports = new FleetService();
