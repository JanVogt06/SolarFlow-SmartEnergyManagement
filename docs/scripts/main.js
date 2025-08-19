// Import aller Module
import { TerminalAnimation } from './modules/terminal.js';
import { ScrollAnimationObserver } from './modules/scroll.js';
import { initSmoothScroll, initCopyButtons } from './modules/utils.js';
import { CONFIG } from './config.js';

// Initialisierung wenn DOM bereit
document.addEventListener('DOMContentLoaded', () => {
    // Lucide Icons initialisieren
    lucide.createIcons();

    // Terminal Animation starten
    const terminal = new TerminalAnimation();

    // Scroll Animations initialisieren
    const scrollObserver = new ScrollAnimationObserver();

    // Smooth Scroll für Navigation
    initSmoothScroll();

    // Copy Buttons für Code-Blöcke
    initCopyButtons();

    // Optional: Sunlight Effects (wenn gewünscht)
    // import('./modules/sunlight.js').then(module => {
    //     new module.SunlightEffects();
    // });
});

// Global Error Handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e);
});