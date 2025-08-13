// Initialize Lucide Icons
lucide.createIcons();

// Live Display Simulation - Wie das echte Python Rich Display
class TerminalAnimation {
    constructor() {
        this.container = document.querySelector('.terminal-body');
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
            { name: 'Wärmepumpe', priority: 1, power: 500, status: 'off', runtime: 0 },
            { name: 'Waschmaschine', priority: 3, power: 2000, status: 'off', runtime: 0 },
            { name: 'Pool-Pumpe', priority: 7, power: 800, status: 'off', runtime: 0 }
        ];
        this.init();
    }

    init() {
        this.container.innerHTML = '';
        this.container.style.cssText = 'padding: 15px; font-family: monospace; color: #e2e8f0;';
        this.render();
        this.startSimulation();
    }

    render() {
        // Zeit-Variable entfernt, da nicht verwendet
        // Alternative: Wenn du die Zeit anzeigen möchtest, füge sie im Display hinzu

        // Display direkt in innerHTML setzen ohne Zwischenvariable
        this.container.innerHTML = `
<div class="live-display">
    <div class="display-section">
        <div class="section-title" style="color: #fbbf24">⚡ Leistungsdaten</div>
        <div class="data-row">
            <span class="label">PV-Erzeugung:</span>
            <span class="value ${this.getColorClass(this.values.pvPower, 'pv')}">${this.values.pvPower.toFixed(0)} W</span>
        </div>
        <div class="data-row">
            <span class="label">Hausverbrauch:</span>
            <span class="value">${this.values.loadPower.toFixed(0)} W</span>
        </div>
        <div class="data-row">
            <span class="label">${this.values.gridPower >= 0 ? 'Netzbezug:' : 'Einspeisung:'}</span>
            <span class="value ${this.values.gridPower >= 0 ? 'red' : 'green'}">${Math.abs(this.values.gridPower).toFixed(0)} W</span>
        </div>
        <div class="data-row">
            <span class="label">Batterie ${this.values.batteryPower >= 0 ? '→' : '←'}:</span>
            <span class="value ${this.values.batteryPower >= 0 ? 'green' : 'yellow'}">${Math.abs(this.values.batteryPower).toFixed(0)} W</span>
        </div>
        <div class="data-row">
            <span class="label">Ladestand:</span>
            <span class="battery-bar">${this.createBatteryBar(this.values.batterySoc)}</span>
            <span class="value ${this.getColorClass(this.values.batterySoc, 'battery')}">${this.values.batterySoc.toFixed(1)}%</span>
        </div>
    </div>

    <div class="display-section">
        <div class="section-title" style="color: #10b981">📊 Kennzahlen</div>
        <div class="data-row">
            <span class="label">Eigenverbrauch:</span>
            <span class="value">${this.values.selfConsumption.toFixed(0)} W</span>
        </div>
        <div class="data-row">
            <span class="label">Autarkiegrad:</span>
            <span class="value ${this.getColorClass(this.values.autarky, 'autarky')}">${this.values.autarky.toFixed(1)}%</span>
        </div>
        <div class="data-row">
            <span class="label">Überschuss:</span>
            <span class="value ${this.values.surplus > 100 ? 'yellow' : ''}">${this.values.surplus.toFixed(0)} W</span>
        </div>
    </div>

    <div class="display-section">
        <div class="section-title" style="color: #f59e0b">🔌 Gerätesteuerung (${this.devices.filter(d => d.status === 'on').length} aktiv)</div>
        <div class="device-table">
            ${this.devices.map(device => `
                <div class="device-row">
                    <span class="device-name">${device.name}</span>
                    <span class="device-prio">[P${device.priority}]</span>
                    <span class="device-power">${device.power}W</span>
                    <span class="device-status ${device.status === 'on' ? 'status-on' : 'status-off'}">${device.status === 'on' ? '● EIN' : '○ AUS'}</span>
                    <span class="device-runtime">${this.formatRuntime(device.runtime)}</span>
                </div>
            `).join('')}
        </div>
        <div class="data-row" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #334155">
            <span class="label">Gesteuerter Verbrauch:</span>
            <span class="value yellow">${this.devices.filter(d => d.status === 'on').reduce((sum, d) => sum + d.power, 0)} W</span>
        </div>
    </div>

    <div class="display-footer">
        <span style="color: #10b981">💰 Ersparnis heute: ${this.values.savings.toFixed(2)}€</span>
    </div>
</div>`;
    }

    createBatteryBar(soc) {
        const width = 20;
        const filled = Math.round(soc / 100 * width);
        const bar = '█'.repeat(filled) + '░'.repeat(width - filled);
        return `[${bar}]`;
    }

    getColorClass(value, type) {
        if (type === 'pv') return value > 3000 ? 'green' : value > 1000 ? 'yellow' : '';
        if (type === 'battery') return value > 80 ? 'green' : value > 30 ? 'yellow' : 'red';
        if (type === 'autarky') return value > 75 ? 'green' : value > 50 ? 'yellow' : 'red';
        return '';
    }

    formatRuntime(minutes) {
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return `${h}h ${m.toString().padStart(2, '0')}m`;
    }

    startSimulation() {
        // Update values every 2 seconds
        setInterval(() => {
            // Simulate PV curve (more realistic)
            const hour = new Date().getHours();
            const dayFactor = Math.sin(Math.max(0, (hour - 6) / 12 * Math.PI));

            // PV Power: 0-6000W depending on time of day with more variation
            this.values.pvPower = Math.max(0,
                (5000 * dayFactor + (Math.random() - 0.5) * 2000) *
                (0.7 + Math.random() * 0.6) // Cloud factor
            );

            // Base load varies more realistically
            const baseLoad = 800 + Math.random() * 1200; // 800-2000W base

            // Device control simulation
            let deviceConsumption = 0;
            this.devices.forEach(device => {
                // Only switch on if we have enough surplus
                if (device.status === 'off' && this.values.surplus > device.power + 200) {
                    device.status = 'on';
                } else if (device.status === 'on' && this.values.surplus < 100) {
                    device.status = 'off';
                }

                if (device.status === 'on') {
                    device.runtime += 2/60;
                    deviceConsumption += device.power;
                }
            });

            // Total load = base + devices
            this.values.loadPower = baseLoad + deviceConsumption;

            // Battery logic (simplified but realistic)
            let batteryContribution = 0;

            if (this.values.pvPower > this.values.loadPower && this.values.batterySoc < 95) {
                // Charge battery with surplus
                const surplus = this.values.pvPower - this.values.loadPower;
                this.values.batteryPower = -Math.min(surplus * 0.9, 2500);
                this.values.batterySoc = Math.min(100, this.values.batterySoc + 0.3);
                batteryContribution = 0; // Charging, not contributing
            } else if (this.values.pvPower < this.values.loadPower && this.values.batterySoc > 20) {
                // Discharge battery to help
                const deficit = this.values.loadPower - this.values.pvPower;
                this.values.batteryPower = Math.min(deficit * 0.9, 2500);
                this.values.batterySoc = Math.max(0, this.values.batterySoc - 0.2);
                batteryContribution = this.values.batteryPower;
            } else {
                this.values.batteryPower = 0;
                batteryContribution = 0;
            }

            // CORRECT CALCULATIONS
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

            /*
            // Debug log
            console.log({
                pv: this.values.pvPower.toFixed(0),
                load: this.values.loadPower.toFixed(0),
                battery: batteryContribution.toFixed(0),
                selfCons: this.values.selfConsumption.toFixed(0),
                autarky: this.values.autarky.toFixed(1)
            });
            */

            this.render();
        }, 2000);
    }
}

// Smooth Scroll für Navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Start animations when page loads
document.addEventListener('DOMContentLoaded', () => {
    new TerminalAnimation();
    lucide.createIcons();

    // Add copy buttons to code blocks
    const codeBlocks = document.querySelectorAll('.code-block');

    codeBlocks.forEach(block => {
        // Create copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.innerHTML = '<i data-lucide="copy"></i>';
        copyBtn.title = 'Code kopieren';

        // Position relative to code block
        block.style.position = 'relative';
        block.appendChild(copyBtn);

        // Initialize icon
        lucide.createIcons();

        // Copy functionality
        copyBtn.addEventListener('click', () => {
            const code = block.querySelector('code, pre').textContent;
            navigator.clipboard.writeText(code).then(() => {
                copyBtn.innerHTML = '<i data-lucide="check"></i>';
                lucide.createIcons(); // Re-initialize for new icon

                setTimeout(() => {
                    copyBtn.innerHTML = '<i data-lucide="copy"></i>';
                    lucide.createIcons(); // Re-initialize again
                }, 2000);
            });
        });
    });
});