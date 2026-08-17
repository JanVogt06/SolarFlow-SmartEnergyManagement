import { DashboardController } from './modules/dashboard.js';
import { DevicesController } from './modules/devices.js';
import { StatisticsController } from './modules/statistic.js';
import { SettingsController } from './modules/settings.js';
import { TabController } from './modules/tabs.js';
import { ApiClient } from './modules/api.js';
import { updateConnectionStatus } from './modules/utils.js';

class SolarFlowApp {
    constructor() {
        this.api = new ApiClient();
        this.controllers = {};
        this.updateInterval = 5000;
        this.intervalId = null;
        this.isConnected = false;

        this.init();
    }

    async init() {
        try {
            if (window.lucide) {
                lucide.createIcons();
            }

            this.tabController = new TabController(this.onTabChange.bind(this));

            this.controllers.dashboard = new DashboardController(this.api);
            this.controllers.devices = new DevicesController(this.api);
            this.controllers.statistics = new StatisticsController(this.api);
            this.controllers.settings = new SettingsController(this.api, this.onSettingsChange.bind(this));

            this.initHelpModal();
            this.updateInterval = parseInt(localStorage.getItem('updateInterval')) || this.updateInterval;

            await this.startUpdates();
            this.setupEventListeners();
        } catch (error) {
            console.error('Failed to initialize app:', error);
            updateConnectionStatus(false);
            this.showHelpModal();
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
                this.restartUpdates();
            });
        }

        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                this.hideHelpModal();
                this.tabController.switchTab('settings');
            });
        }

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
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });

        window.addEventListener('online', () => this.resumeUpdates());
        window.addEventListener('offline', () => {
            this.isConnected = false;
            updateConnectionStatus(false);
            this.pauseUpdates();
            this.showHelpModal();
        });
    }

    onTabChange(tabName) {
        if (this.controllers[tabName] && this.controllers[tabName].onActivate) {
            this.controllers[tabName].onActivate();
        }
    }

    onSettingsChange(settings) {
        this.updateInterval = settings.updateInterval;
        this.api.setBaseUrl(settings.apiUrl);
        this.restartUpdates();
    }

    async updateAll() {
        try {
            this.updateTimestamp();

            const [currentData, devicesData, statsData] = await Promise.all([
                this.api.getCurrentData(),
                this.api.getDevices(),
                this.api.getStats()
            ]);

            this.controllers.dashboard.update(currentData);
            this.controllers.devices.update(devicesData);
            this.controllers.statistics.update(statsData);
            this.controllers.dashboard.updateStats(statsData);

            if (!this.isConnected) {
                this.isConnected = true;
                updateConnectionStatus(true);
                this.hideHelpModal();
            }
        } catch (error) {
            console.error('Update error:', error);
            this.isConnected = false;
            updateConnectionStatus(false);
            this.showHelpModal();
        }
    }

    async startUpdates() {
        await this.updateAll();
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
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new SolarFlowApp();
});