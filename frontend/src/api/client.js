const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = {
  // Helper to handle standard JSON API responses
  async _handleResponse(response) {
    if (!response.ok) {
      let message = 'An error occurred';
      try {
        const errData = await response.json();
        message = errData.detail || errData.message || message;
      } catch (e) {
        // Fallback to text if JSON parse fails
        try {
          message = await response.text();
        } catch (_) {}
      }
      throw new Error(message);
    }
    return response.json();
  },

  // Authentication API Routes
  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include', // Crucial for receiving HttpOnly session cookie
    });
    return this._handleResponse(response);
  },

  async register(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include',
    });
    return this._handleResponse(response);
  },

  async logout() {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    return this._handleResponse(response);
  },

  async getCurrentUser() {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      credentials: 'include',
    });
    return this._handleResponse(response);
  },

  // Assessment Management Routes
  async submitAssessment(file, metadataJson) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadataJson));

    const response = await fetch(`${API_BASE_URL}/assess`, {
      method: 'POST',
      body: formData,
      credentials: 'include', // Uses cookie session authentication for UI
    });
    return this._handleResponse(response);
  },

  async getAssessmentStatus(assessmentId) {
    const response = await fetch(`${API_BASE_URL}/assess/${assessmentId}`, {
      method: 'GET',
      credentials: 'include',
    });
    return this._handleResponse(response);
  },

  async getHealth() {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) throw new Error('Failed to check backend health');
    return response.json();
  }
};
