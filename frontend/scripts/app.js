// App Hauptlogik
class SolarFlowApp {
    constructor() {
        this.api = new SolarAPI();
        this.charts = new ChartManager();
        this.updateInterval = 5000;
        this.intervalId = null;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSettings();
        this.startUpdates();
    }

    setupEventListeners() {
        // Tab Navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Settings
        document.getElementById('update-interval')?.addEventListener('change', (e) => {
            this.updateInterval = parseInt(e.target.value);
            this.restartUpdates();
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
    }

    async startUpdates() {
        // Initial update
        await this.updateAll();

        // Set interval
        this.intervalId = setInterval(() => this.updateAll(), this.updateInterval);
    }

    restartUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        this.startUpdates();
    }

    async updateAll() {
        try {
            // Get current data
            const data = await this.api.getCurrentData();
            if (data) {
                this.updateOverview(data);
                this.charts.updatePowerChart(data);
                this.setConnectionStatus(true);
            }

            // Get stats
            const stats = await this.api.getStats();
            if (stats) {
                this.updateStatistics(stats);
            }

            // Get devices
            const devices = await this.api.getDevices();
            if (devices) {
                this.updateDevices(devices);
            }

            // Update timestamp
            this.updateTimestamp();

        } catch (error) {
            console.error('Update error:', error);
            this.setConnectionStatus(false);
        }
    }

    updateOverview(data) {
        // Power values
        this.updateElement('pv-power', `${Math.round(data.pv_power)} W`);
        this.updateElement('load-power', `${Math.round(data.load_power)} W`);

        // Grid
        const gridCard = document.getElementById('grid-card');
        const gridPower = data.grid_power;

        if (gridPower < 0) {
            this.updateElement('grid-label', 'Einspeisung');
            this.updateElement('grid-power', `${Math.abs(Math.round(gridPower))} W`);
            this.updateElement('grid-arrow', '→');
            gridCard?.classList.add('feeding');
            gridCard?.classList.remove('consuming');
        } else {
            this.updateElement('grid-label', 'Netzbezug');
            this.updateElement('grid-power', `${Math.round(gridPower)} W`);
            this.updateElement('grid-arrow', '←');
            gridCard?.classList.add('consuming');
            gridCard?.classList.remove('feeding');
        }

        // Battery
        if (data.has_battery && data.battery_soc !== null) {
            document.getElementById('battery-card').style.display = 'block';
            this.updateElement('battery-soc', `${Math.round(data.battery_soc)}%`);

            const batteryFill = document.getElementById('battery-fill');
            if (batteryFill) {
                batteryFill.style.width = `${data.battery_soc}%`;
            }
        } else {
            document.getElementById('battery-card').style.display = 'none';
        }

        // Metrics
        this.updateElement('autarky-rate', `${Math.round(data.autarky_rate)}%`);
        this.updateElement('surplus-power', `${Math.round(data.surplus_power)} W`);

        // Surplus status
        const surplusStatus = document.getElementById('surplus-status');
        if (surplusStatus) {
            if (data.surplus_power > 1000) {
                surplusStatus.textContent = 'Hoher Überschuss';
                surplusStatus.style.color = 'var(--success-color)';
            } else if (data.surplus_power > 100) {
                surplusStatus.textContent = 'Moderater Überschuss';
                surplusStatus.style.color = 'var(--warning-color)';
            } else {
                surplusStatus.textContent = 'Kein Überschuss';
                surplusStatus.style.color = 'var(--text-secondary)';
            }
        }

        // Update autarky chart
        this.charts.updateAutarkyGauge(data.autarky_rate);
    }

    updateStatistics(stats) {
        this.updateElement('stats-date', new Date(stats.date).toLocaleDateString('de-DE'));
        this.updateElement('stat-pv-energy', `${stats.pv_energy.toFixed(2)} kWh`);
        this.updateElement('stat-consumption', `${stats.consumption_energy.toFixed(2)} kWh`);
        this.updateElement('stat-self-consumption', `${stats.self_consumption_energy.toFixed(2)} kWh`);
        this.updateElement('stat-grid-energy', `${stats.grid_energy.toFixed(2)} kWh`);
        this.updateElement('stat-feed-in', `${stats.feed_in_energy.toFixed(2)} kWh`);
        this.updateElement('stat-autarky-avg', `${stats.autarky_avg.toFixed(1)} %`);

        // Costs
        this.updateElement('cost-saved', `${stats.cost_saved.toFixed(2)} €`);
        this.updateElement('total-benefit', `Gesamt: ${stats.total_benefit.toFixed(2)} €`);
        this.updateElement('stat-cost-saved', `${stats.cost_saved.toFixed(2)} €`);
        this.updateElement('stat-total-benefit', `${stats.total_benefit.toFixed(2)} €`);

        // Daily energy for overview
        this.updateElement('daily-energy', `${stats.pv_energy.toFixed(1)} kWh`);
        this.updateElement('feed-in-energy', `${stats.feed_in_energy.toFixed(1)} kWh`);
    }

    updateDevices(data) {
        const grid = document.getElementById('devices-grid');
        if (!grid) return;

        // Summary
        const activeDevices = data.devices.filter(d => d.state === 'on').length;
        this.updateElement('active-devices', activeDevices);
        this.updateElement('total-consumption', `${Math.round(data.total_consumption)} W`);

        // Clear and rebuild grid
        grid.innerHTML = '';

        data.devices.forEach(device => {
            const card = document.createElement('div');
            card.className = `device-card ${device.state === 'on' ? 'active' : ''}`;

            card.innerHTML = `
                <div class="device-header">
                    <span class="device-name">${device.name}</span>
                    <span class="device-status ${device.state}">${this.getDeviceStatusText(device.state)}</span>
                </div>
                <div class="device-info">
                    <div class="device-info-row">
                        <span>Leistung:</span>
                        <span>${device.power_consumption} W</span>
                    </div>
                    <div class="device-info-row">
                        <span>Priorität:</span>
                        <span>${device.priority}</span>
                    </div>
                    <div class="device-info-row">
                        <span>Laufzeit heute:</span>
                        <span>${this.formatRuntime(device.runtime_today)}</span>
                    </div>
                    <div class="device-info-row">
                        <span>Schwellwerte:</span>
                        <span>Ein: ${device.switch_on_threshold}W / Aus: ${device.switch_off_threshold}W</span>
                    </div>
                </div>
            `;

            grid.appendChild(card);
        });

        // Show info if no devices
        if (data.devices.length === 0) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary);">Keine Geräte konfiguriert</p>';
        }
    }

    getDeviceStatusText(state) {
        const states = {
            'on': 'EIN',
            'off': 'AUS',
            'blocked': 'BLOCKIERT'
        };
        return states[state] || state;
    }

    formatRuntime(minutes) {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return `${hours}h ${mins}m`;
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateTimestamp() {
        const now = new Date();
        this.updateElement('last-update', now.toLocaleTimeString('de-DE'));
    }

    setConnectionStatus(online) {
        const status = document.getElementById('connection-status');
        if (status) {
            if (online) {
                status.classList.add('online');
                status.querySelector('.status-text').textContent = 'Verbunden';
            } else {
                status.classList.remove('online');
                status.querySelector('.status-text').textContent = 'Getrennt';
            }
        }
    }

    loadSettings() {
        const savedUrl = localStorage.getItem('apiUrl');
        if (savedUrl) {
            document.getElementById('api-url').value = savedUrl;
            this.api.baseUrl = savedUrl;
        }

        const savedInterval = localStorage.getItem('updateInterval');
        if (savedInterval) {
            document.getElementById('update-interval').value = savedInterval;
            this.updateInterval = parseInt(savedInterval);
        }
    }
}

// Settings functions
function saveSettings() {
    const apiUrl = document.getElementById('api-url').value;
    const updateInterval = document.getElementById('update-interval').value;

    localStorage.setItem('apiUrl', apiUrl);
    localStorage.setItem('updateInterval', updateInterval);

    // Reload to apply settings
    location.reload();
}

// Start app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new SolarFlowApp();
});