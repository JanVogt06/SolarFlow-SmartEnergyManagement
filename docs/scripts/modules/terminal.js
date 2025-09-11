export class TerminalAnimation {
    constructor() {
        this.container = document.querySelector('.terminal-body');
        this.currentLang = this.getCurrentLanguage();

        // Device names in both languages
        this.deviceNames = {
            en: {
                heatPump: 'Heat Pump',
                washingMachine: 'Washing Machine',
                poolPump: 'Pool Pump'
            },
            de: {
                heatPump: 'Wärmepumpe',
                washingMachine: 'Waschmaschine',
                poolPump: 'Pool-Pumpe'
            }
        };

        // Labels in both languages
        this.labels = {
            en: {
                powerData: '⚡ Power Data',
                pvGeneration: 'PV Generation:',
                consumption: 'House Consumption:',
                gridFeedIn: 'Grid Feed-in:',
                gridDraw: 'Grid Draw:',
                batteryCharge: 'Battery ↑:',
                batteryDischarge: 'Battery ↓:',
                batteryLevel: 'Battery Level:',
                metrics: '📊 Metrics',
                selfConsumption: 'Self-consumption:',
                autarky: 'Self-sufficiency:',
                surplus: 'Surplus:',
                deviceControl: '🔌 Device Control',
                active: 'active',
                controlledConsumption: 'Controlled Consumption:',
                savingsToday: '💰 Savings today:',
                statusOn: '● ON',
                statusOff: '○ OFF'
            },
            de: {
                powerData: '⚡ Leistungsdaten',
                pvGeneration: 'PV-Erzeugung:',
                consumption: 'Hausverbrauch:',
                gridFeedIn: 'Einspeisung:',
                gridDraw: 'Netzbezug:',
                batteryCharge: 'Batterie ↑:',
                batteryDischarge: 'Batterie ↓:',
                batteryLevel: 'Ladestand:',
                metrics: '📊 Kennzahlen',
                selfConsumption: 'Eigenverbrauch:',
                autarky: 'Autarkiegrad:',
                surplus: 'Überschuss:',
                deviceControl: '🔌 Gerätesteuerung',
                active: 'aktiv',
                controlledConsumption: 'Gesteuerter Verbrauch:',
                savingsToday: '💰 Ersparnis heute:',
                statusOn: '● EIN',
                statusOff: '○ AUS'
            }
        };

        this.values = {
            pvPower: 0,
            loadPower: 0,
            gridPower: 0,
            batteryPower: 0,
            batterySoc: 75,
            selfConsumption: 0,
            autarky: 0,
            surplus: 0,
            savings: 0
        };

        this.devices = [
            {
                nameKey: 'heatPump',
                priority: 1,
                power: 500,
                status: 'off',
                runtime: 0,
                lastSwitch: null,
                switchOnThreshold: 700,
                switchOffThreshold: 100
            },
            {
                nameKey: 'washingMachine',
                priority: 3,
                power: 2000,
                status: 'off',
                runtime: 0,
                lastSwitch: null,
                switchOnThreshold: 2200,
                switchOffThreshold: 200
            },
            {
                nameKey: 'poolPump',
                priority: 7,
                power: 800,
                status: 'off',
                runtime: 0,
                lastSwitch: null,
                switchOnThreshold: 1000,
                switchOffThreshold: 150
            }
        ];

        this.hysteresisTime = 5 * 60 * 1000; // 5 minutes

        // Listen for language changes
        window.addEventListener('languageChanged', (e) => {
            this.currentLang = e.detail.lang;
            this.render();
        });

        this.init();
    }

    getCurrentLanguage() {
        return localStorage.getItem('language') || 'en';
    }

    getLabel(key) {
        return this.labels[this.currentLang][key] || this.labels['en'][key];
    }

    getDeviceName(device) {
        return this.deviceNames[this.currentLang][device.nameKey] || this.deviceNames['en'][device.nameKey];
    }

    init() {
        this.container.innerHTML = '';
        this.container.style.cssText = 'padding: 15px; font-family: monospace; color: #e2e8f0;';
        this.render();
        this.startSimulation();
    }

    render() {
        const activeDevices = this.devices.filter(d => d.status === 'on');
        const controlledPower = activeDevices.reduce((sum, d) => sum + d.power, 0);
        const currencySymbol = this.currentLang === 'de' ? '€' : '$';

        this.container.innerHTML = `
<div class="live-display">
    <div class="display-section">
        <div class="section-terminal-title" style="color: #fbbf24">${this.getLabel('powerData')}</div>
        <div class="data-row">
            <span class="label">${this.getLabel('pvGeneration')}</span>
            <span class="value ${this.getColorClass(this.values.pvPower, 'pv')}">${this.values.pvPower.toFixed(0)} W</span>
        </div>
        <div class="data-row">
            <span class="label">${this.getLabel('consumption')}</span>
            <span class="value">${this.values.loadPower.toFixed(0)} W</span>
        </div>
        <div class="data-row">
            <span class="label">${this.values.gridPower >= 0 ? this.getLabel('gridDraw') : this.getLabel('gridFeedIn')}</span>
            <span class="value ${this.values.gridPower >= 0 ? 'red' : 'green'}">${Math.abs(this.values.gridPower).toFixed(0)} W</span>
        </div>
        <div class="data-row">
            <span class="label">${this.values.batteryPower >= 0 ? this.getLabel('batteryCharge') : this.getLabel('batteryDischarge')}</span>
            <span class="value ${this.values.batteryPower >= 0 ? 'green' : 'yellow'}">${Math.abs(this.values.batteryPower).toFixed(0)} W</span>
        </div>
        <div class="data-row">
            <span class="label">${this.getLabel('batteryLevel')}</span>
            <span class="battery-bar">${this.createBatteryBar(this.values.batterySoc)}</span>
            <span class="value ${this.getColorClass(this.values.batterySoc, 'battery')}">${this.values.batterySoc.toFixed(1)}%</span>
        </div>
    </div>

    <div class="display-section">
        <div class="section-terminal-title" style="color: #10b981">${this.getLabel('metrics')}</div>
        <div class="data-row">
            <span class="label">${this.getLabel('selfConsumption')}</span>
            <span class="value">${this.values.selfConsumption.toFixed(0)} W</span>
        </div>
        <div class="data-row">
            <span class="label">${this.getLabel('autarky')}</span>
            <span class="value ${this.getColorClass(this.values.autarky, 'autarky')}">${this.values.autarky.toFixed(1)}%</span>
        </div>
        <div class="data-row">
            <span class="label">${this.getLabel('surplus')}</span>
            <span class="value ${this.values.surplus > 100 ? 'yellow' : ''}">${this.values.surplus.toFixed(0)} W</span>
        </div>
    </div>

    <div class="display-section">
        <div class="section-terminal-title" style="color: #f59e0b">${this.getLabel('deviceControl')} (${activeDevices.length} ${this.getLabel('active')})</div>
        <div class="device-table">
            ${this.devices.map(device => `
                <div class="device-row">
                    <span class="device-name">${this.getDeviceName(device)}</span>
                    <span class="device-prio">[P${device.priority}]</span>
                    <span class="device-power">${device.power}W</span>
                    <span class="device-status ${device.status === 'on' ? 'status-on' : 'status-off'}">${device.status === 'on' ? this.getLabel('statusOn') : this.getLabel('statusOff')}</span>
                    <span class="device-runtime">${this.formatRuntime(device.runtime)}</span>
                </div>
            `).join('')}
        </div>
        <div class="data-row" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #334155">
            <span class="label">${this.getLabel('controlledConsumption')}</span>
            <span class="value yellow">${controlledPower} W</span>
        </div>
    </div>

    <div class="display-footer">
        <span style="color: #10b981">${this.getLabel('savingsToday')} ${currencySymbol}${this.values.savings.toFixed(2)}</span>
    </div>
</div>`;
    }

    createBatteryBar(soc) {
        const color = soc > 80 ? '#10b981' : soc > 30 ? '#fbbf24' : '#ef4444';

        return `
        <span style="
            display: inline-block;
            width: 100px;
            height: 8px;
            border: 1px solid #64748b;
            border-radius: 2px;
            background: rgba(255,255,255,0.05);
            position: relative;
            overflow: hidden;
            vertical-align: middle;
        ">
            <span style="
                display: block;
                height: 100%;
                width: ${soc}%;
                background: ${color};
                transition: width 0.3s ease;
            "></span>
        </span>
    `;
    }

    getColorClass(value, type) {
        if (type === 'pv') return value > 3000 ? 'green' : value > 1000 ? 'yellow' : '';
        if (type === 'battery') return value > 80 ? 'green' : value > 30 ? 'yellow' : 'red';
        if (type === 'autarky') return value > 75 ? 'green' : value > 50 ? 'yellow' : 'red';
        return '';
    }

    formatRuntime(minutes) {
        const roundedMinutes = Math.round(minutes * 100) / 100;
        const h = Math.floor(roundedMinutes / 60);
        const m = Math.floor(roundedMinutes % 60);
        return `${h}h ${m.toString().padStart(2, '0')}m`;
    }

    canSwitchDevice(device) {
        if (!device.lastSwitch) return true;
        const timeSinceLastSwitch = Date.now() - device.lastSwitch;
        return timeSinceLastSwitch >= this.hysteresisTime;
    }

    startSimulation() {
        setInterval(() => {
            // Simulate PV curve
            const hour = new Date().getHours();
            const dayFactor = Math.sin(Math.max(0, (hour - 6) / 12 * Math.PI));

            this.values.pvPower = Math.max(0,
                (5000 * dayFactor + (Math.random() - 0.5) * 2000) *
                (0.7 + Math.random() * 0.6)
            );

            const baseLoad = 800 + Math.random() * 1200;
            let deviceConsumption = 0;

            const sortedDevices = [...this.devices].sort((a, b) => a.priority - b.priority);

            sortedDevices.forEach(device => {
                const canSwitch = this.canSwitchDevice(device);

                if (device.status === 'off' &&
                    this.values.surplus > device.switchOnThreshold &&
                    canSwitch) {
                    device.status = 'on';
                    device.lastSwitch = Date.now();
                }
                else if (device.status === 'on' &&
                    this.values.surplus < device.switchOffThreshold &&
                    canSwitch) {
                    device.status = 'off';
                    device.lastSwitch = Date.now();
                }

                if (device.status === 'on') {
                    device.runtime += 2/60;
                    deviceConsumption += device.power;
                }
            });

            this.values.loadPower = baseLoad + deviceConsumption;

            // Battery logic - fixed redundant initializer
            let batteryContribution;

            if (this.values.pvPower > this.values.loadPower && this.values.batterySoc < 95) {
                const surplus = this.values.pvPower - this.values.loadPower;
                this.values.batteryPower = -Math.min(surplus * 0.9, 2500);
                this.values.batterySoc = Math.min(100, this.values.batterySoc + 0.3);
                batteryContribution = 0;
            } else if (this.values.pvPower < this.values.loadPower && this.values.batterySoc > 20) {
                const deficit = this.values.loadPower - this.values.pvPower;
                this.values.batteryPower = Math.min(deficit * 0.9, 2500);
                this.values.batterySoc = Math.max(0, this.values.batterySoc - 0.2);
                batteryContribution = this.values.batteryPower;
            } else {
                this.values.batteryPower = 0;
                batteryContribution = 0;
            }

            // Total available power from our sources
            const ownProduction = this.values.pvPower + batteryContribution;

            // How much of our consumption is covered by our own production
            this.values.selfConsumption = Math.min(this.values.loadPower, ownProduction);

            // Grid power (positive = buying, negative = selling)
            this.values.gridPower = this.values.loadPower - ownProduction;

            // Surplus (only when we produce more than we consume)
            this.values.surplus = Math.max(0, ownProduction - this.values.loadPower);

            // AUTARKIE: Percentage of consumption covered by own sources
            if (this.values.loadPower > 0) {
                this.values.autarky = Math.min(100,
                    (this.values.selfConsumption / this.values.loadPower) * 100
                );
            } else {
                this.values.autarky = 100;
            }

            // Add some variation to make it more realistic
            this.values.autarky = Math.max(0, Math.min(100,
                this.values.autarky + (Math.random() - 0.5) * 5
            ));

            // Calculate savings
            this.values.savings += (this.values.selfConsumption / 1000 * 0.40 / 1800);

            this.render();
        }, 2000);
    }
}