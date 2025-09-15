export class StatisticsController {
    constructor(api) {
        this.api = api;
        this.elements = this.cacheElements();
    }

    cacheElements() {
        return {
            statsDate: document.getElementById('stats-date'),
            pvEnergy: document.getElementById('stat-pv-energy'),
            consumption: document.getElementById('stat-consumption'),
            selfConsumption: document.getElementById('stat-self-consumption'),
            gridEnergy: document.getElementById('stat-grid-energy'),
            feedIn: document.getElementById('stat-feed-in'),
            autarkyAvg: document.getElementById('stat-autarky-avg'),
            costSaved: document.getElementById('stat-cost-saved'),
            totalBenefit: document.getElementById('stat-total-benefit')
        };
    }

    update(stats) {
        if (!stats) return;

        // Update date with animation
        this.updateDate();

        // Update all statistics with stagger animation
        this.updateStat('pvEnergy', `${stats.pv_energy.toFixed(1)} kWh`, 0);
        this.updateStat('consumption', `${stats.consumption_energy.toFixed(1)} kWh`, 100);
        this.updateStat('selfConsumption', `${stats.self_consumption_energy.toFixed(1)} kWh`, 200);
        this.updateStat('gridEnergy', `${stats.grid_energy.toFixed(1)} kWh`, 300);
        this.updateStat('feedIn', `${stats.feed_in_energy.toFixed(1)} kWh`, 400);
        this.updateStat('autarkyAvg', `${stats.autarky_avg.toFixed(1)} %`, 500);

        // Update cost summary with special animation
        this.updateCostSummary(stats);
    }

    updateDate() {
        if (!this.elements.statsDate) return;

        const now = new Date();
        const dateStr = now.toLocaleDateString('de-DE', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        this.elements.statsDate.textContent = dateStr;
        this.elements.statsDate.classList.add('updating');
        setTimeout(() => this.elements.statsDate.classList.remove('updating'), 300);
    }

    updateStat(key, value, delay) {
        const element = this.elements[key];
        if (!element) return;
        element.textContent = value;
    }

    updateCostSummary(stats) {
        const costSavedEl = this.elements.costSaved;
        const totalBenefitEl = this.elements.totalBenefit;

        if (costSavedEl) {
            this.animateCounter(costSavedEl, stats.cost_saved, '€', 2);
        }

        if (totalBenefitEl) {
            this.animateCounter(totalBenefitEl, stats.total_benefit, '€', 2);
        }

        // Add glow effect to cost summary card
        const costCard = document.querySelector('.cost-summary-card');
        if (costCard) {
            costCard.classList.add('pulse-glow');
            setTimeout(() => costCard.classList.remove('pulse-glow'), 2000);
        }
    }

    animateCounter(element, targetValue, suffix = '', decimals = 0) {
        if (!element) return;

        const startValue = parseFloat(element.textContent) || 0;
        const duration = 1000;
        const steps = 30;
        const stepDuration = duration / steps;
        const increment = (targetValue - startValue) / steps;

        let current = startValue;
        let step = 0;

        const timer = setInterval(() => {
            step++;
            current += increment;

            if (step >= steps) {
                current = targetValue;
                clearInterval(timer);
            }

            element.textContent = `${current.toFixed(decimals)} ${suffix}`;
        }, stepDuration);
    }

    onActivate() {
        // Called when statistics tab is activated
        if (this.api) {
            this.api.getStats().then(stats => this.update(stats));
        }
    }
}