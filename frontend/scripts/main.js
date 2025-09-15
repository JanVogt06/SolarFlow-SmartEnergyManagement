import { DashboardController } from './modules/dashboard.js';
import { DevicesController } from './modules/devices.js';
import { StatisticsController } from './modules/statistic.js';
import { SettingsController } from './modules/settings.js';
import { TabController } from './modules/tabs.js';
import { ApiClient } from './modules/api.js';
import { initUtils, updateConnectionStatus } from './modules/utils.js';

class SolarFlowApp {
    constructor() {
        this.api = new ApiClient();
        this.controllers = {};
        this.updateInterval = 5000;
        this.intervalId = null;
        this.isConnected = false;  // NEU: Verbindungsstatus tracken
        this.connectionCheckCounter = 0;  // NEU: Fehler-Counter

        this.init();
    }

    async init() {
        try {
            // Initialize Lucide Icons
            if (window.lucide) {
                lucide.createIcons();
            }

            // Initialize utilities
            initUtils();

            // Initialize Tab Controller
            this.tabController = new TabController(this.onTabChange.bind(this));

            // Initialize Controllers
            this.controllers.dashboard = new DashboardController(this.api);
            this.controllers.devices = new DevicesController(this.api);
            this.controllers.statistics = new StatisticsController(this.api);
            this.controllers.settings = new SettingsController(this.api, this.onSettingsChange.bind(this));

            // Load saved settings
            this.loadSettings();

            // Start data updates
            await this.startUpdates();

            // Set up event listeners
            this.setupEventListeners();

            console.log('SolarFlow App initialized successfully');
        } catch (error) {
            console.error('Failed to initialize app:', error);
            updateConnectionStatus(false);
        }
    }

    setupEventListeners() {
        // Visibility change - pause/resume updates
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });

        // Network status
        window.addEventListener('online', () => this.resumeUpdates());
        window.addEventListener('offline', () => {
            this.isConnected = false;  // GEÄNDERT
            updateConnectionStatus(false);
            this.pauseUpdates();
        });
    }

    onTabChange(tabName) {
        // Trigger specific controller updates when tab changes
        if (this.controllers[tabName] && this.controllers[tabName].onActivate) {
            this.controllers[tabName].onActivate();
        }
    }

    onSettingsChange(settings) {
        // Update interval if changed
        if (settings.updateInterval && settings.updateInterval !== this.updateInterval) {
            this.updateInterval = settings.updateInterval;
            this.restartUpdates();
        }

        // Update API URL if changed
        if (settings.apiUrl) {
            this.api.setBaseUrl(settings.apiUrl);
            this.restartUpdates();
        }
    }

    async updateAll() {
        try {

            // Update timestamp
            this.updateTimestamp();

            // Get current data
            const currentData = await this.api.getCurrentData();
            if (currentData) {
                this.controllers.dashboard.update(currentData);

                // Verbindung ist gut - nur updaten wenn Status sich ändert
                if (!this.isConnected) {
                    this.isConnected = true;
                    updateConnectionStatus(true);
                }
                this.connectionCheckCounter = 0;  // Reset error counter
            }

            // Get devices data
            const devicesData = await this.api.getDevices();
            if (devicesData) {
                this.controllers.devices.update(devicesData);
            }

            // Get statistics
            const statsData = await this.api.getStats();
            if (statsData) {
                this.controllers.statistics.update(statsData);
                // Update dashboard stats
                this.controllers.dashboard.updateStats(statsData);
            }
        } catch (error) {
            console.error('Update error:', error);

            // NEU: Nur als getrennt markieren nach mehreren Fehlversuchen
            this.connectionCheckCounter++;
            if (this.connectionCheckCounter >= 3 && this.isConnected) {
                this.isConnected = false;
                updateConnectionStatus(false);
            }
        }
    }

    async startUpdates() {
        // Initial update
        await this.updateAll();

        // Set up interval
        this.intervalId = setInterval(() => this.updateAll(), this.updateInterval);
    }

    pauseUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    resumeUpdates() {
        if (!this.intervalId) {
            this.startUpdates();
        }
    }

    restartUpdates() {
        this.pauseUpdates();
        this.startUpdates();
    }

    updateTimestamp() {
        const element = document.getElementById('last-update');
        if (element) {
            const now = new Date();
            element.textContent = now.toLocaleTimeString('de-DE');
        }
    }

    loadSettings() {
        const savedUrl = localStorage.getItem('apiUrl');
        if (savedUrl) {
            this.api.setBaseUrl(savedUrl);
        }

        const savedInterval = localStorage.getItem('updateInterval');
        if (savedInterval) {
            this.updateInterval = parseInt(savedInterval);
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new SolarFlowApp();
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e);
});