export const translations = {
    en: {
        'nav.brand': 'Smart Energy Manager',
        'nav.features': 'Features',
        'nav.quickstart': 'Quick Start',
        'hero.subtitle': 'Intelligent control of your solar system with Python',
        'hero.btn.start': 'Start now',

        'problem.title': 'The Problem',
        'problem.quote': '"I\'m giving away 60% of my solar power to the grid"',
        'problem.item1': 'Low feed-in tariff (8 cents/kWh)',
        'problem.item2': 'High electricity prices (40 cents/kWh)',
        'problem.item3': 'Manual device control inefficient',

        'solution.title': 'The Solution',
        'solution.quote': '"I use 85% myself thanks to intelligent control"',
        'solution.item1': 'Automatic device control',
        'solution.item2': 'Priority-based activation',
        'solution.item3': 'Maximum self-consumption',

        'features.title': 'Features',
        'features.subtitle': 'Everything you need for optimal self-consumption',

        'features.monitoring.title': 'Live Monitoring',
        'features.monitoring.item1': 'Real-time data from inverter',
        'features.monitoring.item2': 'Self-sufficiency calculation',
        'features.monitoring.item3': 'Daily statistics',
        'features.monitoring.item4': 'CSV export for analysis',

        'features.automation.title': 'Intelligent Automation',
        'features.automation.item1': 'Priority-based control',
        'features.automation.item2': 'Hysteresis logic',
        'features.automation.item3': 'Time window management',
        'features.automation.item4': 'Min/Max runtimes',

        'features.savings.title': 'Cost Optimization',
        'features.savings.item1': 'Day/Night tariffs',
        'features.savings.item2': 'Savings calculation',
        'features.savings.item3': 'ROI tracking',
        'features.savings.item4': 'Monthly reports',

        'quickstart.title': 'Quick Start',
        'quickstart.subtitle': 'More self-consumption in 3 steps',
        'quickstart.step1.title': 'Installation',
        'quickstart.step1.desc': 'Clone the repository and install dependencies',
        'quickstart.step2.title': 'Configuration',
        'quickstart.step2.desc': 'Adjust config.yaml to your system',
        'quickstart.step3.title': 'Start',
        'quickstart.step3.desc': 'Start the Energy Manager',
        'quickstart.info.text': 'Detailed instructions and documentation can be found in the',
        'quickstart.info.wiki': 'Wiki'
    },
    de: {
        'nav.brand': 'Smart Energy Manager',
        'nav.features': 'Features',
        'nav.quickstart': 'Quick Start',
        'hero.subtitle': 'Intelligente Steuerung Ihrer Solaranlage mit Python',
        'hero.btn.start': 'Jetzt starten',

        'problem.title': 'Das Problem',
        'problem.quote': '"Ich verschenke 60% meines Solarstroms ans Netz"',
        'problem.item1': 'Niedrige Einspeisevergütung (8 Cent/kWh)',
        'problem.item2': 'Hohe Strompreise (40 Cent/kWh)',
        'problem.item3': 'Manuelle Gerätesteuerung ineffizient',

        'solution.title': 'Die Lösung',
        'solution.quote': '"Ich nutze 85% selbst dank intelligenter Steuerung"',
        'solution.item1': 'Automatische Gerätesteuerung',
        'solution.item2': 'Prioritätsbasierte Einschaltung',
        'solution.item3': 'Maximaler Eigenverbrauch',

        'features.title': 'Features',
        'features.subtitle': 'Alles was du für optimalen Eigenverbrauch brauchst',

        'features.monitoring.title': 'Live Monitoring',
        'features.monitoring.item1': 'Echtzeit-Daten vom Wechselrichter',
        'features.monitoring.item2': 'Autarkiegrad-Berechnung',
        'features.monitoring.item3': 'Tagesstatistiken',
        'features.monitoring.item4': 'CSV-Export für Analysen',

        'features.automation.title': 'Intelligente Automation',
        'features.automation.item1': 'Prioritätsbasierte Steuerung',
        'features.automation.item2': 'Hysterese-Logik',
        'features.automation.item3': 'Zeitfenster-Verwaltung',
        'features.automation.item4': 'Min/Max Laufzeiten',

        'features.savings.title': 'Kostenoptimierung',
        'features.savings.item1': 'Tag/Nacht-Tarife',
        'features.savings.item2': 'Einsparungsberechnung',
        'features.savings.item3': 'ROI-Tracking',
        'features.savings.item4': 'Monatliche Reports',

        'quickstart.title': 'Quick Start',
        'quickstart.subtitle': 'In 3 Schritten zu mehr Eigenverbrauch',
        'quickstart.step1.title': 'Installation',
        'quickstart.step1.desc': 'Clone das Repository und installiere die Abhängigkeiten',
        'quickstart.step2.title': 'Konfiguration',
        'quickstart.step2.desc': 'Passe die config.yaml an deine Anlage an',
        'quickstart.step3.title': 'Start',
        'quickstart.step3.desc': 'Starte den Energy Manager',
        'quickstart.info.text': 'Detaillierte Anleitung und Dokumentation findest du im',
        'quickstart.info.wiki': 'Wiki'
    }
};

// Config examples for each language
export const configExamples = {
    en: `{
    "name": "Washing Machine",
    "description": "Washing Machine Basement",
    "power_consumption": 2000,
    "priority": 3,
    "min_runtime": 90,
    "max_runtime_per_day": 0,
    "switch_on_threshold": 2100,
    "switch_off_threshold": 100,
    "allowed_time_ranges": [
        ["08:00", "20:00"]
    ]
}`,
    de: `{
    "name": "Waschmaschine",
    "description": "Waschmaschine Keller",
    "power_consumption": 2000,
    "priority": 3,
    "min_runtime": 90,
    "max_runtime_per_day": 0,
    "switch_on_threshold": 2100,
    "switch_off_threshold": 100,
    "allowed_time_ranges": [
        ["08:00", "20:00"]
    ]
}`
};

// Translation System Class - NACH den Daten definiert
export class TranslationSystem {
    constructor() {
        this.translations = translations;
        this.configExamples = configExamples;
        this.currentLang = this.getCurrentLanguage();
        this.init();
    }

    init() {
        // Set initial language
        this.setLanguage(this.currentLang);

        // Setup language switcher click handler
        this.setupLanguageSwitcher();
    }

    setupLanguageSwitcher() {
        const switcher = document.getElementById('language-switcher');
        if (switcher) {
            switcher.addEventListener('click', () => {
                this.toggleLanguage();
            });
        }
    }

    getCurrentLanguage() {
        const saved = localStorage.getItem('language');
        if (saved) return saved;

        // Detect browser language
        const browserLang = navigator.language || navigator.userLanguage;
        return browserLang.startsWith('de') ? 'de' : 'en';
    }

    setLanguage(lang) {
        // Update all elements with data-i18n attribute
        const elements = document.querySelectorAll('[data-i18n]');

        elements.forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (this.translations[lang][key]) {
                el.textContent = this.translations[lang][key];
            }
        });

        // Update config example
        const configEl = document.getElementById('config-example');
        if (configEl) {
            configEl.textContent = this.configExamples[lang];
        }

        // Update language indicator
        const langIndicator = document.getElementById('current-lang');
        if (langIndicator) {
            langIndicator.textContent = lang.toUpperCase();
        }

        // Update HTML lang attribute
        document.documentElement.lang = lang;

        // Update meta description
        const metaDesc = document.querySelector('meta[name="description"]');
        if (metaDesc) {
            metaDesc.content = lang === 'de'
                ? 'Smart Energy Manager - Maximiere deinen Solar-Eigenverbrauch automatisch'
                : 'Smart Energy Manager - Maximize your solar self-consumption automatically';
        }

        // Save preference
        localStorage.setItem('language', lang);
        this.currentLang = lang;

        // Dispatch event for other modules
        window.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { lang: lang }
        }));
    }

    toggleLanguage() {
        const newLang = this.currentLang === 'en' ? 'de' : 'en';
        this.setLanguage(newLang);
    }

    // Helper method to get current translation
    translate(key) {
        return this.translations[this.currentLang][key] || this.translations['en'][key] || key;
    }
}

// Default export for convenience
export default {
    TranslationSystem,
    translations,
    configExamples
};