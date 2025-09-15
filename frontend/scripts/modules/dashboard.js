export class DashboardController {
    constructor(api) {
        this.api = api;
        this.elements = this.cacheElements();
    }

    cacheElements() {
        return {
            pvPower: document.getElementById('pv-power'),
            loadPower: document.getElementById('load-power'),
            gridPower: document.getElementById('grid-power'),
            gridLabel: document.getElementById('grid-label'),
            gridCard: document.getElementById('grid-card'),
            batterySoc: document.getElementById('battery-soc'),
            batteryCard: document.getElementById('battery-card'),
            autarkyRate: document.getElementById('autarky-rate'),
            surplusPower: document.getElementById('surplus-power'),
            surplusStatus: document.getElementById('surplus-status'),
            costSaved: document.getElementById('cost-saved'),
            totalBenefit: document.getElementById('total-benefit'),
            dailyEnergy: document.getElementById('daily-energy'),
            feedInEnergy: document.getElementById('feed-in-energy')
        };
    }

    update(data) {
        if (!data) return;

        // Update power values with animation
        this.updatePowerValue('pvPower', data.pv_power, 'W');
        this.updatePowerValue('loadPower', data.load_power, 'W');

        // Handle grid power (positive = consuming, negative = feeding)
        this.updateGridStatus(data.grid_power);

        // Handle battery if available
        this.updateBatteryStatus(data);

        // Update metrics
        this.updateMetrics(data);

        // Animate values
        this.animateChanges();
    }

    updateStats(stats) {
        if (!stats) return;

        // Update cost savings with fallback
        if (stats.cost_saved !== undefined && stats.cost_saved !== null) {
            this.updateValue('costSaved', `${stats.cost_saved.toFixed(2)}€`);
        } else {
            this.updateValue('costSaved', '0.00€');
        }

        if (stats.total_benefit !== undefined && stats.total_benefit !== null) {
            this.updateValue('totalBenefit', `Gesamt: ${stats.total_benefit.toFixed(2)}€`);
        } else {
            this.updateValue('totalBenefit', 'Gesamt: 0.00€');
        }

        // Update daily energy with fallback
        if (stats.pv_energy !== undefined && stats.pv_energy !== null) {
            this.updateValue('dailyEnergy', `${stats.pv_energy.toFixed(1)} kWh`);
        } else {
            this.updateValue('dailyEnergy', '0.0 kWh');
        }

        if (stats.feed_in_energy !== undefined && stats.feed_in_energy !== null) {
            this.updateValue('feedInEnergy', `${stats.feed_in_energy.toFixed(1)} kWh`);
        } else {
            this.updateValue('feedInEnergy', '0.0 kWh');
        }
    }

    updatePowerValue(elementId, value, unit) {
        const element = this.elements[elementId];
        if (!element) return;

        const formattedValue = Math.round(value);
        element.textContent = `${formattedValue} ${unit}`;
    }

    updateGridStatus(gridPower) {
        const card = this.elements.gridCard;
        const label = this.elements.gridLabel;
        const power = this.elements.gridPower;

        if (!card || !label || !power) return;

        const isFeeding = gridPower < 0;
        const absolutePower = Math.abs(Math.round(gridPower));

        // Update card classes
        card.classList.toggle('feeding', isFeeding);
        card.classList.toggle('consuming', !isFeeding);

        // Update label and value
        label.textContent = isFeeding ? 'Einspeisung' : 'Netzbezug';
        power.textContent = `${absolutePower} W`;

        // Add pulse animation for significant power
        if (absolutePower > 1000) {
            card.classList.add('high-power');
        } else {
            card.classList.remove('high-power');
        }
    }

    updateBatteryStatus(data) {
        const card = this.elements.batteryCard;
        const soc = this.elements.batterySoc;

        if (!card || !soc) return;

        if (data.has_battery && data.battery_soc !== null) {
            card.style.display = 'block';
            const socValue = Math.round(data.battery_soc);
            soc.textContent = `${socValue}%`;

            // Update battery icon based on SOC
            this.updateBatteryIcon(socValue);

            // Add warning class for low battery
            card.classList.toggle('low-battery', socValue < 20);
            card.classList.toggle('full-battery', socValue > 95);
        } else {
            card.style.display = 'none';
        }
    }

    updateBatteryIcon(soc) {
        const card = this.elements.batteryCard;
        if (!card) return;

        const iconElement = card.querySelector('.flow-icon svg');
        if (!iconElement) return;

        // Update icon based on SOC level
        let iconName = 'battery';
        if (soc <= 20) iconName = 'battery-low';
        else if (soc >= 80) iconName = 'battery-full';
        else iconName = 'battery-medium';

        // Update lucide icon
        iconElement.setAttribute('data-lucide', iconName);
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    updateMetrics(data) {
        // Autarky rate with color coding
        const autarky = Math.round(data.autarky_rate);
        this.updateValue('autarkyRate', `${autarky}%`);
        this.updateAutarkyColor(autarky);

        // Surplus power
        const surplus = Math.round(data.surplus_power);
        this.updateValue('surplusPower', `${surplus} W`);
        this.updateSurplusStatus(surplus);
    }

    updateAutarkyColor(value) {
        const element = this.elements.autarkyRate;
        if (!element) return;

        element.classList.remove('low', 'medium', 'high');
        if (value >= 75) {
            element.classList.add('high');
        } else if (value >= 50) {
            element.classList.add('medium');
        } else {
            element.classList.add('low');
        }
    }

    updateSurplusStatus(surplus) {
        const element = this.elements.surplusStatus;
        if (!element) return;

        let status = '';
        let className = '';

        if (surplus > 2000) {
            status = 'Sehr hoher Überschuss';
            className = 'very-high';
        } else if (surplus > 1000) {
            status = 'Hoher Überschuss';
            className = 'high';
        } else if (surplus > 100) {
            status = 'Moderater Überschuss';
            className = 'moderate';
        } else {
            status = 'Kein Überschuss';
            className = 'none';
        }

        element.textContent = status;
        element.className = 'metric-subtext ' + className;
    }

    updateValue(elementId, value) {
        const element = this.elements[elementId];
        if (element && element.textContent !== value) {
            element.textContent = value;
        }
    }

    animateChanges() {
        // Add subtle animations to changed values
        Object.values(this.elements).forEach(element => {
            if (element && element.classList.contains('updating')) {
                element.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    element.style.transform = 'scale(1)';
                }, 150);
            }
        });
    }
}