import { TerminalAnimation } from './modules/terminal.js';
import { ScrollAnimationObserver } from './modules/scroll.js';
import { initSmoothScroll, initCopyButtons } from './modules/utils.js';
import { TranslationSystem } from './modules/translations.js';

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Translation System and make it globally available
    window.translationSystem = new TranslationSystem();

    // Initialize Lucide Icons
    lucide.createIcons();

    // Start Terminal Animation (self-initializing)
    new TerminalAnimation();

    // Initialize Scroll Animations (self-initializing)
    new ScrollAnimationObserver();

    // Initialize Smooth Scroll for Navigation
    initSmoothScroll();

    // Initialize Copy Buttons for Code Blocks
    initCopyButtons();

    // Re-create icons after language change
    window.addEventListener('languageChanged', () => {
        lucide.createIcons();
    });
});

// Global Error Handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e);
});