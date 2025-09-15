export class SettingsController {
    constructor(api, onSettingsChange) {
        this.api = api;
        this.onSettingsChange = onSettingsChange;
        this.elements = this.cacheElements();
        this.init();
    }

    cacheElements() {
        return {
            apiUrl: document.getElementById('api-url'),
            updateInterval: document.getElementById('update-interval'),
            saveButton: document.getElementById('save-settings')
        };
    }

    init() {
        this.loadSettings();
        this.setupEventListeners();
        this.applySettingsAnimation();
    }

    setupEventListeners() {
        if (this.elements.saveButton) {
            this.elements.saveButton.addEventListener('click', () => this.saveSettings());
        }

        // Add input validation
        if (this.elements.apiUrl) {
            this.elements.apiUrl.addEventListener('input', () => {
                this.validateApiUrl();
            });
        }
    }

    loadSettings() {
        // Load saved settings
        const apiUrl = localStorage.getItem('apiUrl') || 'http://localhost:8000';
        const updateInterval = localStorage.getItem('updateInterval') || '5000';

        if (this.elements.apiUrl) {
            this.elements.apiUrl.value = apiUrl;
        }

        if (this.elements.updateInterval) {
            this.elements.updateInterval.value = updateInterval;
        }
    }

    async saveSettings() {
        const button = this.elements.saveButton;

        // Add loading state
        button.classList.add('loading');
        button.innerHTML = '<i data-lucide="loader"></i> Speichere...';
        lucide.createIcons();

        try {
            const settings = {
                apiUrl: this.elements.apiUrl.value,
                updateInterval: parseInt(this.elements.updateInterval.value)
            };

            // Validate settings
            if (!this.validateSettings(settings)) {
                throw new Error('Ungültige Einstellungen');
            }

            // Save to localStorage
            localStorage.setItem('apiUrl', settings.apiUrl);
            localStorage.setItem('updateInterval', settings.updateInterval);

            // Test connection
            await this.testConnection(settings.apiUrl);

            // Notify parent
            if (this.onSettingsChange) {
                this.onSettingsChange(settings);
            }

            // Success feedback
            this.showSuccess();

        } catch (error) {
            this.showError(error.message);
        } finally {
            // Reset button
            setTimeout(() => {
                button.classList.remove('loading');
                button.innerHTML = '<i data-lucide="save"></i> Speichern';
                lucide.createIcons();
            }, 1000);
        }
    }

    validateSettings(settings) {
        // Validate API URL
        try {
            new URL(settings.apiUrl);
        } catch {
            this.showFieldError('apiUrl', 'Ungültige URL');
            return false;
        }

        // Validate interval
        if (settings.updateInterval < 1000 || settings.updateInterval > 60000) {
            this.showFieldError('updateInterval', 'Intervall muss zwischen 1-60 Sekunden liegen');
            return false;
        }

        return true;
    }

    validateApiUrl() {
        const input = this.elements.apiUrl;
        const value = input.value;

        try {
            new URL(value);
            input.classList.remove('error');
            input.classList.add('valid');
        } catch {
            input.classList.remove('valid');
            input.classList.add('error');
        }
    }

    async testConnection(url) {
        const testUrl = `${url}/api/status`;
        const response = await fetch(testUrl, {
            method: 'GET',
            signal: AbortSignal.timeout(5000)
        });

        if (!response.ok) {
            throw new Error('Verbindung fehlgeschlagen');
        }
    }

    showSuccess() {
        this.showNotification('Einstellungen erfolgreich gespeichert', 'success');

        // Add success animation to cards
        document.querySelectorAll('.settings-card').forEach(card => {
            card.classList.add('success-pulse');
            setTimeout(() => card.classList.remove('success-pulse'), 1000);
        });
    }

    showError(message) {
        this.showNotification(message || 'Fehler beim Speichern', 'error');
    }

    showFieldError(fieldId, message) {
        const field = this.elements[fieldId];
        if (!field) return;

        field.classList.add('error');

        // Show error message
        const errorEl = document.createElement('div');
        errorEl.className = 'field-error';
        errorEl.textContent = message;
        field.parentElement.appendChild(errorEl);

        setTimeout(() => {
            errorEl.remove();
        }, 3000);
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;

        const icon = type === 'success' ? 'check-circle' :
                     type === 'error' ? 'alert-circle' : 'info';

        notification.innerHTML = `
            <i data-lucide="${icon}"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(notification);
        lucide.createIcons();

        // Auto remove
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    applySettingsAnimation() {
        // Apply stagger animation to settings cards
        const cards = document.querySelectorAll('.settings-card');
        cards.forEach((card, index) => {
            card.style.transitionDelay = `${index * 0.1}s`;
        });
    }

    onActivate() {
        // Called when settings tab is activated
        this.applySettingsAnimation();
    }
}