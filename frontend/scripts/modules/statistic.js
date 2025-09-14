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
        this.updateStatWithAnimation('pvEnergy', `${stats.pv_energy.toFixed(1)} kWh`, 0);
        this.updateStatWithAnimation('consumption', `${stats.consumption_energy.toFixed(1)} kWh`, 100);
        this.updateStatWithAnimation('selfConsumption', `${stats.self_consumption_energy.toFixed(1)} kWh`, 200);
        this.updateStatWithAnimation('gridEnergy', `${stats.grid_energy.toFixed(1)} kWh`, 300);
        this.updateStatWithAnimation('feedIn', `${stats.feed_in_energy.toFixed(1)} kWh`, 400);
        this.updateStatWithAnimation('autarkyAvg', `${stats.autarky_average.toFixed(1)} %`, 500);

        // Update cost summary with special animation
        this.updateCostSummary(stats);

        // Apply card animations
        this.applyCardAnimations();
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

    updateStatWithAnimation(key, value, delay) {
        const element = this.elements[key];
        if (!element) return;

        setTimeout(() => {
            element.classList.add('updating');
            element.style.transform = 'scale(0.95)';

            setTimeout(() => {
                element.textContent = value;
                element.style.transform = 'scale(1.05)';

                setTimeout(() => {
                    element.style.transform = 'scale(1)';
                    element.classList.remove('updating');
                }, 150);
            }, 150);
        }, delay);
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

    applyCardAnimations() {
        // Apply scroll animations to all stat cards
        const cards = document.querySelectorAll('.stat-card');
        cards.forEach((card, index) => {
            card.classList.add('scroll-fade-in-up', 'scroll-stagger');
            setTimeout(() => {
                card.classList.add('scroll-visible');
            }, index * 100);
        });
    }

    onActivate() {
        // Called when statistics tab is activated
        this.applyCardAnimations();

        if (this.api) {
            this.api.getStats().then(stats => this.update(stats));
        }
    }
}