// Flexible API service layer decoupled from the components
// Follows SOLID principles: components shouldn't care how the data is fetched.
const API_BASE_URL = 'http://localhost:8081/api';

class ApiService {
  async fetchFleet() {
    try {
      const response = await fetch(`${API_BASE_URL}/vehicles`);
      if (!response.ok) throw new Error('Network response was not ok');
      const json = await response.json();
      return json; // Spring boot returns list directly, not { data: [] }
    } catch (error) {
      console.error('Error fetching fleet:', error);
      throw error;
    }
  }

  async addVehicle(vehicleData) {
    try {
      const response = await fetch(`${API_BASE_URL}/vehicles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(vehicleData)
      });
      if (!response.ok) {
        throw new Error('Failed to add vehicle');
      }
      const json = await response.json();
      return json;
    } catch (error) {
      console.error('Error adding vehicle:', error);
      throw error;
    }
  }

  async removeVehicle(vehicleId) {
    try {
      const response = await fetch(`${API_BASE_URL}/vehicles/${vehicleId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to remove vehicle');
      return true;
    } catch (error) {
      console.error('Error removing vehicle:', error);
      throw error;
    }
  }
}

export const apiService = new ApiService();
