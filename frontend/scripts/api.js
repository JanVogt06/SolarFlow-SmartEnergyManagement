// API Client
class SolarAPI {
    constructor() {
        this.baseUrl = localStorage.getItem('apiUrl') || 'http://localhost:8000';
    }

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    async getCurrentData() {
        return this.request('/api/current');
    }

    async getStats() {
        return this.request('/api/stats');
    }

    async getDevices() {
        return this.request('/api/devices');
    }

    async toggleDevice(deviceName) {
        return this.request(`/api/devices/${deviceName}/toggle`, {
            method: 'POST'
        });
    }

    async getStatus() {
        return this.request('/api/status');
    }
}