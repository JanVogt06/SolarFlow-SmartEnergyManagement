import { showNotification } from './utils.js';

// Einstellungsname der API -> Eingabefeld im Formular
const SERVER_FIELDS = {
    fronius_ip: { id: 'fronius-ip', type: 'text' },
    update_interval: { id: 'poll-interval', type: 'number' },
    enable_hue: { id: 'enable-hue', type: 'checkbox' },
    hue_bridge_ip: { id: 'hue-bridge-ip', type: 'text' },
    electricity_price: { id: 'electricity-price', type: 'number' },
    electricity_price_night: { id: 'electricity-price-night', type: 'number' },
    feed_in_tariff: { id: 'feed-in-tariff', type: 'number' },
    hysteresis_minutes: { id: 'hysteresis-minutes', type: 'number' },
    manual_override_minutes: { id: 'manual-override-minutes', type: 'number' },
    min_battery_soc_on: { id: 'battery-soc-on', type: 'number' },
    min_battery_soc_off: { id: 'battery-soc-off', type: 'number' }
};

export class SettingsController {
    constructor(api, onSettingsChange) {
        this.api = api;
        this.onSettingsChange = onSettingsChange;

        this.elements = {
            apiUrl: document.getElementById('api-url'),
            updateInterval: document.getElementById('update-interval'),
            saveButton: document.getElementById('save-settings')
        };
        this.serverInputs = Object.fromEntries(
            Object.entries(SERVER_FIELDS).map(([name, field]) => [name, document.getElementById(field.id)])
        );

        this.init();
    }

    init() {
        this.loadClientSettings();
        this.loadServerSettings();
        this.setupEventListeners();
    }

    setupEventListeners() {
        if (this.elements.saveButton) {
            this.elements.saveButton.addEventListener('click', () => this.saveSettings());
        }

        if (this.elements.apiUrl) {
            this.elements.apiUrl.addEventListener('input', () => this.validateApiUrl());
        }
    }

    loadClientSettings() {
        // Standard ist die Adresse, unter der das Dashboard selbst geladen wurde
        if (this.elements.apiUrl) {
            this.elements.apiUrl.value = localStorage.getItem('apiUrl') || window.location.origin;
        }
        if (this.elements.updateInterval) {
            this.elements.updateInterval.value = localStorage.getItem('updateInterval') || '5000';
        }
    }

    async loadServerSettings() {
        try {
            this.applyServerSettings(await this.api.getSettings());
        } catch (error) {
            console.warn('Server-Einstellungen konnten nicht geladen werden:', error);
        }
    }

    applyServerSettings(settings) {
        if (!settings) return;

        for (const [name, field] of Object.entries(SERVER_FIELDS)) {
            const input = this.serverInputs[name];
            const value = settings[name];
            if (!input || value === undefined || value === null) continue;

            if (field.type === 'checkbox') {
                input.checked = Boolean(value);
            } else {
                input.value = value;
            }
        }
    }

    readServerSettings() {
        const payload = {};

        for (const [name, field] of Object.entries(SERVER_FIELDS)) {
            const input = this.serverInputs[name];
            if (!input) continue;

            if (field.type === 'checkbox') {
                payload[name] = input.checked;
            } else if (field.type === 'number') {
                if (input.value !== '') payload[name] = parseFloat(input.value);
            } else if (input.value.trim()) {
                payload[name] = input.value.trim();
            }
        }

        return payload;
    }

    readClientSettings() {
        return {
            apiUrl: this.elements.apiUrl.value.trim(),
            updateInterval: parseInt(this.elements.updateInterval.value)
        };
    }

    async saveSettings() {
        const button = this.elements.saveButton;
        button.disabled = true;
        button.innerHTML = '<i data-lucide="loader"></i> Speichere...';
        lucide.createIcons();

        try {
            const client = this.readClientSettings();
            this.validateClientSettings(client);

            // Erst testen, dann speichern - sonst blockiert eine falsche URL die ganze App
            await this.testConnection(client.apiUrl);
            localStorage.setItem('apiUrl', client.apiUrl);
            localStorage.setItem('updateInterval', client.updateInterval);

            const response = await this.api.updateSettings(this.readServerSettings());
            this.applyServerSettings(response.settings);

            if (this.onSettingsChange) {
                this.onSettingsChange(client);
            }

            showNotification('Einstellungen gespeichert', 'success');
        } catch (error) {
            showNotification(error.message || 'Fehler beim Speichern', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = '<i data-lucide="save"></i> Speichern';
            lucide.createIcons();
        }
    }

    validateClientSettings(settings) {
        try {
            new URL(settings.apiUrl);
        } catch {
            throw new Error('Server URL ist keine gültige Adresse');
        }

        if (!(settings.updateInterval >= 1000 && settings.updateInterval <= 60000)) {
            throw new Error('Aktualisierung muss zwischen 1 und 60 Sekunden liegen');
        }
    }

    validateApiUrl() {
        const input = this.elements.apiUrl;

        try {
            new URL(input.value);
            input.classList.remove('error');
            input.classList.add('valid');
        } catch {
            input.classList.remove('valid');
            input.classList.add('error');
        }
    }

    async testConnection(url) {
        let response;
        try {
            response = await fetch(`${url}/api/status`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
        } catch {
            throw new Error(`Server unter ${url} nicht erreichbar`);
        }

        if (!response.ok) {
            throw new Error(`Server antwortet mit HTTP ${response.status}`);
        }
    }

    onActivate() {
        this.loadServerSettings();
    }
}
