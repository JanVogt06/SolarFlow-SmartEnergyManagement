// Initialize Lucide Icons
lucide.createIcons();

// Terminal Animation
class TerminalAnimation {
    constructor() {
        this.container = document.querySelector('.terminal-body');
        this.outputs = [
            { text: '$ python main.py --ip 192.168.178.90', class: 'terminal-command', delay: 0 },
            { text: '═══════════════════════════════════════════════════════════════════════════════', class: 'terminal-separator', delay: 500 },
            { text: 'SOLAR MONITOR - v1.0.0', class: 'terminal-header', delay: 100 },
            { text: '═══════════════════════════════════════════════════════════════════════════════', class: 'terminal-separator', delay: 100 },
            { text: '', class: '', delay: 200 },
            { text: '[INFO] Verbinde zu Fronius Wechselrichter...', class: 'terminal-info', delay: 300 },
            { text: '[OK] Verbindung erfolgreich!', class: 'terminal-success', delay: 800 },
            { text: '', class: '', delay: 200 },
            { text: 'LIVE DATEN:', class: 'terminal-header', delay: 300 },
            { text: '├─ PV-Erzeugung:     4,235 W', class: 'terminal-data', delay: 100, dynamic: true },
            { text: '├─ Hausverbrauch:    1,847 W', class: 'terminal-data', delay: 100 },
            { text: '├─ Überschuss:       2,388 W', class: 'terminal-highlight', delay: 100, dynamic: true },
            { text: '└─ Autarkiegrad:     85.3 %', class: 'terminal-success', delay: 100 },
            { text: '', class: '', delay: 400 },
            { text: '[GERÄT] Prüfe Waschmaschine...', class: 'terminal-info', delay: 500 },
            { text: '[AUTO] ✓ Waschmaschine eingeschaltet (2000W)', class: 'terminal-action', delay: 600 },
            { text: '[UPDATE] Überschuss: 388 W', class: 'terminal-update', delay: 300 },
            { text: '', class: '', delay: 400 },
            { text: 'TAGESSTATISTIK:', class: 'terminal-header', delay: 300 },
            { text: '├─ Produktion:       18.4 kWh', class: 'terminal-data', delay: 100 },
            { text: '├─ Eigenverbrauch:   15.6 kWh', class: 'terminal-data', delay: 100 },
            { text: '├─ Einspeisung:      2.8 kWh', class: 'terminal-data', delay: 100 },
            { text: '└─ Ersparnis heute:  4.82 €', class: 'terminal-money', delay: 100 },
        ];
        this.currentIndex = 0;
        this.lines = [];
        this.init();
    }

    init() {
        // Clear container
        this.container.innerHTML = '';
        this.container.style.fontFamily = 'Courier New, monospace';
        this.showNextLine();
    }

    showNextLine() {
        if (this.currentIndex >= this.outputs.length) {
            // Restart after pause
            setTimeout(() => {
                this.currentIndex = 0;
                this.lines = [];
                this.container.innerHTML = '';
                this.showNextLine();
            }, 3000);
            return;
        }

        const output = this.outputs[this.currentIndex];

        setTimeout(() => {
            this.addLine(output.text, output.class, output.dynamic);
            this.currentIndex++;
            this.showNextLine();
        }, output.delay);
    }

    addLine(text, className, isDynamic) {
        const line = document.createElement('div');
        line.className = `terminal-line ${className}`;

        if (isDynamic && text.includes(':')) {
            // Animate number changes for dynamic values
            this.animateValue(line, text);
        } else {
            // Type out the text
            this.typeText(line, text);
        }

        this.container.appendChild(line);
        this.lines.push(line);

        // Keep only last 15 lines visible
        if (this.lines.length > 15) {
            const oldLine = this.lines.shift();
            oldLine.style.opacity = '0';
            setTimeout(() => oldLine.remove(), 300);
        }

        // Scroll to bottom
        this.container.scrollTop = this.container.scrollHeight;
    }

    typeText(element, text, speed = 20) {
        let index = 0;
        const type = () => {
            if (index < text.length) {
                element.textContent = text.substring(0, index + 1);
                index++;
                setTimeout(type, speed);
            }
        };
        type();
    }

    animateValue(element, text) {
        element.textContent = text;
        // Add pulse effect for dynamic values
        element.style.animation = 'pulse 0.5s ease-in-out';
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