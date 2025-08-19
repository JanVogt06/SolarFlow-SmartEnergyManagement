export class ScrollAnimationObserver {
    constructor() {
        this.observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        this.init();
    }

    init() {
        // Erstelle den Intersection Observer
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Element ist sichtbar - füge visible Klasse hinzu
                    entry.target.classList.add('scroll-visible');

                    // FIX: Nach Animation die Animations-Klassen entfernen
                    // damit Hover-Effekte wieder normal funktionieren
                    this.cleanupAfterAnimation(entry.target);
                }
            });
        }, this.observerOptions);

        // Finde alle Elemente mit Animations-Klassen
        this.observeElements();
    }

    cleanupAfterAnimation(element) {
        // Liste der Animations-Klassen die entfernt werden sollen
        const animationClasses = [
            'scroll-fade-in-up',
            'scroll-fade-in-left',
            'scroll-fade-in-right',
            'scroll-scale-in',
            'scroll-rotate-in',
            'scroll-stagger',
            'scroll-hero-entrance',
            'scroll-blur-in',
            'scroll-slide-fade'
        ];

        // Warte bis die Animation fertig ist (max. Animationsdauer ist 1s)
        setTimeout(() => {
            // Entferne alle Animations-Klassen
            animationClasses.forEach(className => {
                element.classList.remove(className);
            });

            // Füge eine Klasse hinzu für normale Hover-Transitions
            element.classList.add('animation-complete');
        }, 1200); // 1.2s um sicher zu sein dass alle Animationen fertig sind
    }

    observeElements() {
        // Liste aller Animation-Klassen
        const animationSelectors = [
            '.scroll-fade-in-up',
            '.scroll-fade-in-left',
            '.scroll-fade-in-right',
            '.scroll-scale-in',
            '.scroll-rotate-in',
            '.scroll-stagger',
            '.scroll-hero-entrance',
            '.scroll-blur-in',
            '.scroll-slide-fade',
        ];

        // Beobachte alle Elemente mit diesen Klassen
        animationSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                this.observer.observe(element);
            });
        });
    }

    // Methode zum manuellen Hinzufügen neuer Elemente
    observe(element) {
        if (element) {
            this.observer.observe(element);
        }
    }

    // Cleanup
    disconnect() {
        this.observer.disconnect();
    }
}