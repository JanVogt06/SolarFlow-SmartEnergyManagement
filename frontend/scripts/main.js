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
        this.isConnected = false;
        this.connectionCheckCounter = 0;
        this.helpModalShown = false;

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

            // Initialize Help Modal
            this.initHelpModal();

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
            this.showHelpModal();  // NEU: Zeige Hilfe bei Initialisierungsfehler
        }
    }

    initHelpModal() {
        const modal = document.getElementById('connection-help-modal');
        const closeBtn = document.getElementById('close-help-modal');
        const retryBtn = document.getElementById('retry-connection');
        const settingsBtn = document.getElementById('open-settings');
        const copyBtns = document.querySelectorAll('.copy-btn');

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideHelpModal());
        }

        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                this.hideHelpModal();
                this.connectionCheckCounter = 0;
                this.restartUpdates();
            });
        }

        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                this.hideHelpModal();
                this.tabController.switchTab('settings');
            });
        }

        // Copy button functionality
        copyBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const textToCopy = btn.dataset.copy;
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const originalIcon = btn.innerHTML;
                    btn.innerHTML = '<i data-lucide="check"></i>';
                    lucide.createIcons();
                    setTimeout(() => {
                        btn.innerHTML = originalIcon;
                        lucide.createIcons();
                    }, 2000);
                });
            });
        });

        // Close modal on overlay click
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target.classList.contains('modal-overlay')) {
                    this.hideHelpModal();
                }
            });
        }
    }

    showHelpModal() {
        const modal = document.getElementById('connection-help-modal');
        if (modal) {
            modal.classList.add('active');
            this.modalVisible = true;
            // Re-initialize icons in modal
            setTimeout(() => lucide.createIcons(), 100);
        }
    }

    hideHelpModal() {
        const modal = document.getElementById('connection-help-modal');
        if (modal) {
            modal.classList.remove('active');
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
            this.isConnected = false;
            updateConnectionStatus(false);
            this.pauseUpdates();
            this.showHelpModal();
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

        // Reset help modal flag when settings change
        this.helpModalShown = false;
    }

    async updateAll() {
        try {
            // Update timestamp
            this.updateTimestamp();

            // Get current data
            const currentData = await this.api.getCurrentData();
            if (currentData) {
                this.controllers.dashboard.update(currentData);

                // Verbindung ist gut
                if (!this.isConnected) {
                    this.isConnected = true;
                    updateConnectionStatus(true);
                    this.hideHelpModal();  // NEU: Verstecke Modal bei erfolgreicher Verbindung
                }
                this.connectionCheckCounter = 0;
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

            // Nur als getrennt markieren nach mehreren Fehlversuchen
            this.connectionCheckCounter++;
            if (this.connectionCheckCounter >= 1 && this.isConnected) {
                this.isConnected = false;
                updateConnectionStatus(false);
                this.showHelpModal();
            } else if (this.connectionCheckCounter >= 1 && !this.isConnected && !this.helpModalShown) {
                this.showHelpModal();
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