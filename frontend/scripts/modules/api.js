export class ApiClient {
    constructor() {
        this.baseUrl = localStorage.getItem('apiUrl') || 'http://localhost:8000';
        this.timeout = 5000;
    }

    setBaseUrl(url) {
        this.baseUrl = url;
        localStorage.setItem('apiUrl', url);
    }

    async request(endpoint, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // API Endpoints
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
        return this.request(`/api/devices/${encodeURIComponent(deviceName)}/toggle`, {
            method: 'POST'
        });
    }
}