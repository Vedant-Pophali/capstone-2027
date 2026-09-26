// Flexible API service layer decoupled from the components
// Follows SOLID principles: components shouldn't care how the data is fetched.
const API_BASE_URL = 'http://localhost:3001/api';

class ApiService {
  async fetchFleet() {
    try {
      const response = await fetch(`${API_BASE_URL}/fleet`);
      if (!response.ok) throw new Error('Network response was not ok');
      const json = await response.json();
      return json.data;
    } catch (error) {
      console.error('Error fetching fleet:', error);
      throw error;
    }
  }

  async addVehicle(vehicleId) {
    try {
      const response = await fetch(`${API_BASE_URL}/fleet/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ vehicleId })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to add vehicle');
      }
      const json = await response.json();
      return json.data;
    } catch (error) {
      console.error('Error adding vehicle:', error);
      throw error;
    }
  }

  async removeVehicle(vehicleId) {
    try {
      const response = await fetch(`${API_BASE_URL}/fleet/${vehicleId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to remove vehicle');
      const json = await response.json();
      return json.data;
    } catch (error) {
      console.error('Error removing vehicle:', error);
      throw error;
    }
  }
}

export const apiService = new ApiService();
