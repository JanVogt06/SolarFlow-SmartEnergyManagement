export class DevicesController {
    constructor(api) {
        this.api = api;
        this.container = document.getElementById('devices-grid');
        this.activeDevicesEl = document.getElementById('active-devices');
        this.totalConsumptionEl = document.getElementById('total-consumption');
        this.devices = [];

        // Modal elements
        this.modal = document.getElementById('add-device-modal');
        this.form = document.getElementById('add-device-form');
        this.timeRangesContainer = document.getElementById('time-ranges-container');

        // Hue elements
        this.hueSection = document.getElementById('hue-section');
        this.hueDeviceSelect = document.getElementById('device-hue-device');
        this.deviceNameInput = document.getElementById('device-name');
        this.hueEnabled = false;
        this.hueDevices = [];

        this.initializeEventListeners();
        this.loadHueConfig();
    }

    initializeEventListeners() {
        // Add device button
        const addDeviceBtn = document.getElementById('add-device-btn');
        if (addDeviceBtn) {
            addDeviceBtn.addEventListener('click', () => this.openModal());
        }

        // Close modal buttons
        const closeBtn = document.getElementById('close-add-device-modal');
        const cancelBtn = document.getElementById('cancel-add-device');
        if (closeBtn) closeBtn.addEventListener('click', () => this.closeModal());
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.closeModal());

        // Close on overlay click
        if (this.modal) {
            const overlay = this.modal.querySelector('.modal-overlay');
            if (overlay) {
                overlay.addEventListener('click', () => this.closeModal());
            }
        }

        // Save device button
        const saveBtn = document.getElementById('save-device');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveDevice());
        }

        // Add time range button
        const addTimeRangeBtn = document.getElementById('add-time-range');
        if (addTimeRangeBtn) {
            addTimeRangeBtn.addEventListener('click', () => this.addTimeRange());
        }

        // Hue device selection - sync name field
        if (this.hueDeviceSelect) {
            this.hueDeviceSelect.addEventListener('change', () => this.onHueDeviceChange());
        }
    }

    onHueDeviceChange() {
        const selectedHueDevice = this.hueDeviceSelect.value;

        if (selectedHueDevice) {
            // Hue-Gerät ausgewählt: Name übernehmen und readonly setzen
            this.deviceNameInput.value = selectedHueDevice;
            this.deviceNameInput.readOnly = true;
            this.deviceNameInput.classList.add('readonly');
        } else {
            // Kein Hue-Gerät: Name editierbar machen
            this.deviceNameInput.readOnly = false;
            this.deviceNameInput.classList.remove('readonly');
        }
    }

    async loadHueConfig() {
        try {
            const hueConfig = await this.api.getHueConfig();
            this.hueEnabled = hueConfig.enabled;
            this.hueDevices = hueConfig.devices || [];

            // Update UI
            if (this.hueSection) {
                this.hueSection.style.display = this.hueEnabled ? 'block' : 'none';
            }

            // Populate Hue device dropdown
            this.populateHueDevices();
        } catch (error) {
            console.warn('Could not load Hue config:', error);
            this.hueEnabled = false;
        }
    }

    populateHueDevices() {
        if (!this.hueDeviceSelect) return;

        // Clear existing options (except first)
        while (this.hueDeviceSelect.options.length > 1) {
            this.hueDeviceSelect.remove(1);
        }

        // Add Hue devices
        this.hueDevices.forEach(device => {
            const option = document.createElement('option');
            option.value = device;
            option.textContent = device;
            this.hueDeviceSelect.appendChild(option);
        });
    }

    openModal() {
        if (this.modal) {
            this.modal.classList.add('active');
            this.resetForm();
            // Refresh Hue config when opening modal
            this.loadHueConfig();
            if (window.lucide) {
                lucide.createIcons();
            }
        }
    }

    closeModal() {
        if (this.modal) {
            this.modal.classList.remove('active');
        }
    }

    resetForm() {
        if (this.form) {
            this.form.reset();
        }
        if (this.timeRangesContainer) {
            this.timeRangesContainer.innerHTML = '';
        }
        // Reset name field to editable
        if (this.deviceNameInput) {
            this.deviceNameInput.readOnly = false;
            this.deviceNameInput.classList.remove('readonly');
        }
    }

    addTimeRange() {
        if (!this.timeRangesContainer) return;

        const timeRangeRow = document.createElement('div');
        timeRangeRow.className = 'time-range-row';
        timeRangeRow.innerHTML = `
            <input type="time" class="time-start" value="06:00" required>
            <span class="time-separator">bis</span>
            <input type="time" class="time-end" value="22:00" required>
            <button type="button" class="remove-time-range">
                <i data-lucide="x"></i>
            </button>
        `;

        // Add remove listener
        const removeBtn = timeRangeRow.querySelector('.remove-time-range');
        removeBtn.addEventListener('click', () => timeRangeRow.remove());

        this.timeRangesContainer.appendChild(timeRangeRow);

        if (window.lucide) {
            lucide.createIcons();
        }
    }

    getTimeRanges() {
        const ranges = [];
        if (!this.timeRangesContainer) return ranges;

        const rows = this.timeRangesContainer.querySelectorAll('.time-range-row');
        rows.forEach(row => {
            const start = row.querySelector('.time-start').value;
            const end = row.querySelector('.time-end').value;
            if (start && end) {
                ranges.push([start + ':00', end + ':00']);
            }
        });
        return ranges;
    }

    async saveDevice() {
        if (!this.form) return;

        // Validate form
        if (!this.form.checkValidity()) {
            this.form.reportValidity();
            return;
        }

        // Get form data
        const formData = new FormData(this.form);
        const device = {
            name: formData.get('name'),
            description: formData.get('description') || '',
            power_consumption: parseInt(formData.get('power_consumption')),
            priority: parseInt(formData.get('priority')),
            switch_on_threshold: parseInt(formData.get('switch_on_threshold')),
            switch_off_threshold: parseInt(formData.get('switch_off_threshold')),
            min_runtime: parseInt(formData.get('min_runtime')) || 0,
            max_runtime_per_day: parseInt(formData.get('max_runtime_per_day')) || 0,
            allowed_time_ranges: this.getTimeRanges()
        };

        // Validate thresholds
        if (device.switch_off_threshold > device.switch_on_threshold) {
            this.showNotification('Ausschalt-Schwellwert darf nicht höher als Einschalt-Schwellwert sein', 'error');
            return;
        }

        try {
            const response = await this.api.createDevice(device);
            if (response) {
                this.showNotification(`Gerät "${device.name}" wurde erfolgreich hinzugefügt`, 'success');
                this.closeModal();
                // Refresh devices list
                const devicesData = await this.api.getDevices();
                this.update(devicesData);
            }
        } catch (error) {
            console.error('Error saving device:', error);
            this.showNotification(error.message || 'Fehler beim Speichern des Geräts', 'error');
        }
    }

    update(devicesData) {
        if (!devicesData || !devicesData.devices) return;

        // Überprüfe, ob alle Geräte einen Status haben
        devicesData.devices.forEach(device => {
            if (!device.state) {
                console.warn(`Gerät ${device.name} hat keinen Status.`);
            }
        });

        this.devices = devicesData.devices;
        this.renderDevices();
        this.updateSummary();
    }

    renderDevices() {
        if (!this.container) return;

        this.container.innerHTML = this.devices.map((device, index) => `
            <div class="device-card ${device.state === 'on' ? 'active' : ''}"
                 data-device="${device.name}"
                 style="transition-delay: ${index * 0.1}s">

                <div class="device-header">
                    <div class="device-info">
                        <h3 class="device-name text-gradient">${device.name}</h3>
                        <p class="device-description">${device.description || ''}</p>
                    </div>
                    <span class="device-status ${device.state}">
                        ${this.getStatusText(device.state)}
                    </span>
                </div>

                <div class="device-metrics">
                    <div class="device-metric">
                        <div class="metric-icon">
                            <i data-lucide="zap"></i>
                        </div>
                        <div class="metric-info">
                            <span class="metric-label">Leistung</span>
                            <span class="metric-value">${device.power_consumption} W</span>
                        </div>
                    </div>

                    <div class="device-metric">
                        <div class="metric-icon">
                            <i data-lucide="activity"></i>
                        </div>
                        <div class="metric-info">
                            <span class="metric-label">Priorität</span>
                            <span class="metric-value">${device.priority}</span>
                        </div>
                    </div>

                    <div class="device-metric">
                        <div class="metric-icon">
                            <i data-lucide="clock"></i>
                        </div>
                        <div class="metric-info">
                            <span class="metric-label">Laufzeit</span>
                            <span class="metric-value">${this.formatRuntime(device.runtime_today)}</span>
                        </div>
                    </div>
                </div>

                <div class="device-thresholds">
                    <div class="threshold-bar">
                        <span class="threshold-label">Ein bei:</span>
                        <span class="threshold-value">${device.switch_on_threshold} W</span>
                    </div>
                    <div class="threshold-bar">
                        <span class="threshold-label">Aus bei:</span>
                        <span class="threshold-value">${device.switch_off_threshold} W</span>
                    </div>
                </div>

                ${device.hysteresis_remaining ? `
                    <div class="device-hysteresis">
                        <i data-lucide="timer"></i>
                        <span>Wartet noch ${this.formatHysteresis(device.hysteresis_remaining)}</span>
                    </div>
                ` : ''}

                ${device.blocked_reason ? `
                    <div class="device-warning">
                        <i data-lucide="alert-triangle"></i>
                        <span>${device.blocked_reason}</span>
                    </div>
                ` : ''}
            </div>
        `).join('');

        // Re-initialize icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    getStatusText(status) {
        const statusMap = {
            'on': 'EIN',
            'off': 'AUS',
            'blocked': 'BLOCKIERT',
            'manual': 'MANUELL'
        };
        return statusMap[status] || status.toUpperCase();
    }

    formatRuntime(minutes) {
        if (!minutes) return '0m';
        const hours = Math.floor(minutes / 60);
        const mins = Math.round(minutes % 60);
        return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
    }

    formatHysteresis(seconds) {
        if (!seconds || seconds <= 0) return '';
        const mins = Math.floor(seconds / 60);
        const secs = Math.round(seconds % 60);
        return mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')} min` : `${secs}s`;
    }

    updateSummary() {
        const activeDevices = this.devices.filter(d => d.state === 'on');
        const totalConsumption = activeDevices.reduce((sum, d) => sum + d.power_consumption, 0);

        if (this.activeDevicesEl) {
            this.animateValue(this.activeDevicesEl, activeDevices.length);
        }

        if (this.totalConsumptionEl) {
            this.animateValue(this.totalConsumptionEl, `${totalConsumption} W`);
        }
    }

    animateValue(element, newValue) {
        element.textContent = newValue;
    }

    showNotification(message, type = 'info') {
        // Notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i data-lucide="${type === 'error' ? 'alert-circle' : 'check-circle'}"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(notification);

        if (window.lucide) {
            lucide.createIcons();
        }

        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    onActivate() {
        // Called when devices tab is activated
        // Simply refresh if needed
    }
}
