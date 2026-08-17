export class TabController {
    constructor(onTabChange) {
        this.onTabChange = onTabChange;
        this.currentTab = 'overview';
        this.init();
    }

    init() {
        this.setupTabListeners();
    }

    setupTabListeners() {
        const tabs = document.querySelectorAll('.nav-tab');

        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = tab.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    switchTab(tabName) {
        if (this.currentTab === tabName) return;

        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });

        this.currentTab = tabName;

        if (this.onTabChange) {
            this.onTabChange(tabName);
        }

        if (window.lucide) {
            setTimeout(() => lucide.createIcons(), 100);
        }
    }
}