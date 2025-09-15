export class DevicesController {
    constructor(api) {
        this.api = api;
        this.container = document.getElementById('devices-grid');
        this.activeDevicesEl = document.getElementById('active-devices');
        this.totalConsumptionEl = document.getElementById('total-consumption');
        this.devices = [];
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
        this.applyAnimations();
    }

    renderDevices() {
        if (!this.container) return;

        this.container.innerHTML = this.devices.map((device, index) => `
            <div class="device-card ${device.state === 'on' ? 'active' : ''} scroll-fade-in-up scroll-stagger" 
                 data-device="${device.name}"
                 style="transition-delay: ${index * 0.1}">
                
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

    applyAnimations() {
        // Trigger scroll animations wie auf der Landingpage
        const cards = this.container.querySelectorAll('.device-card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('scroll-visible');
            }, index * 100);
        });
    }

    showNotification(message, type = 'info') {
        // Notification system wie auf der Landingpage
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} scroll-fade-in-right`;
        notification.innerHTML = `
            <i data-lucide="${type === 'error' ? 'alert-circle' : 'check-circle'}"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    onActivate() {
        // Called when devices tab is activated
        this.applyAnimations();
    }
}