// API service layer — decoupled from React.
// Components never call fetch() directly; they use this service.
// Changing the backend URL or adding auth headers requires changes only here.

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8081/api';

class ApiService {

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const token = localStorage.getItem('fleet_token');
    
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      headers,
      ...options,
    };

    const response = await fetch(url, config);

    // 401 Unauthorized — token expired or revoked; force re-login
    if (response.status === 401) {
      localStorage.removeItem('fleet_token');
      window.location.href = '/login';
      throw new Error('Session expired. Please log in again.');
    }

    if (!response.ok) {
      let errorMessage = `Request failed: ${response.status}`;
      try {
        const errorBody = await response.json();
        errorMessage = errorBody.message || errorMessage;
      } catch { /* response wasn't JSON */ }
      throw new Error(errorMessage);
    }

    // 204 No Content — no body to parse
    if (response.status === 204) return null;

    return response.json();
  }

  // --- Vehicle CRUD ---

  fetchVehicles() {
    return this.request('/vehicles');
  }

  fetchVehicle(id) {
    return this.request(`/vehicles/${id}`);
  }

  createVehicle(data) {
    return this.request('/vehicles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  updateVehicle(id, data) {
    return this.request(`/vehicles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  deleteVehicle(id) {
    return this.request(`/vehicles/${id}`, {
      method: 'DELETE',
    });
  }

  updateVehicleStatus(id, status) {
    return this.request(`/vehicles/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  // --- Dashboard ---

  fetchDashboardStats() {
    return this.request('/dashboard/stats');
  }
}

export const apiService = new ApiService();
