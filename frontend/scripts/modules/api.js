export class ApiClient {
    constructor() {
        this.baseUrl = localStorage.getItem('apiUrl') || window.location.origin;
        this.timeout = 5000;
    }

    setBaseUrl(url) {
        this.baseUrl = url;
        localStorage.setItem('apiUrl', url);
    }

    async request(endpoint, options = {}) {
        const { timeout = this.timeout, ...fetchOptions } = options;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...fetchOptions,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...fetchOptions.headers
                }
            });

            if (!response.ok) {
                throw new Error(await this.readError(response));
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Zeitüberschreitung bei der Serveranfrage');
            }
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        } finally {
            clearTimeout(timeoutId);
        }
    }

    async readError(response) {
        try {
            const body = await response.json();
            if (typeof body.detail === 'string') return body.detail;
            if (Array.isArray(body.detail)) return body.detail.map(d => d.msg).join(', ');
        } catch {
            // Kein JSON-Body - Statuszeile reicht
        }
        return `HTTP ${response.status}: ${response.statusText}`;
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

    async getHueConfig() {
        return this.request('/api/hue');
    }

    async getSettings() {
        return this.request('/api/settings');
    }

    async updateSettings(settings) {
        // Längerer Timeout: ein Wechsel der Hue-Bridge braucht einen Verbindungsaufbau
        return this.request('/api/settings', {
            method: 'PUT',
            body: JSON.stringify(settings),
            timeout: 20000
        });
    }

    async createDevice(device) {
        return this.request('/api/devices', {
            method: 'POST',
            body: JSON.stringify(device)
        });
    }

    async deleteDevice(deviceName) {
        return this.request(`/api/devices/${encodeURIComponent(deviceName)}`, {
            method: 'DELETE'
        });
    }

    async toggleDevice(deviceName) {
        return this.request(`/api/devices/${encodeURIComponent(deviceName)}/toggle`, {
            method: 'POST'
        });
    }

    async releaseManual(deviceName) {
        return this.request(`/api/devices/${encodeURIComponent(deviceName)}/manual`, {
            method: 'DELETE'
        });
    }
}