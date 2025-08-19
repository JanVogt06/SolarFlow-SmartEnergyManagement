export function initSmoothScroll() {
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
}

export function initCopyButtons() {
    const codeBlocks = document.querySelectorAll('.code-block');

    codeBlocks.forEach(block => {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.innerHTML = '<i data-lucide="copy"></i>';
        copyBtn.title = 'Code kopieren';

        block.style.position = 'relative';
        block.appendChild(copyBtn);

        lucide.createIcons();

        copyBtn.addEventListener('click', async () => {
            const code = block.querySelector('code, pre').textContent;

            try {
                await navigator.clipboard.writeText(code);

                copyBtn.innerHTML = '<i data-lucide="check"></i>';
                copyBtn.classList.add('success');
                lucide.createIcons();

                setTimeout(() => {
                    copyBtn.innerHTML = '<i data-lucide="copy"></i>';
                    copyBtn.classList.remove('success');
                    lucide.createIcons();
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
                copyBtn.classList.add('error');
                setTimeout(() => copyBtn.classList.remove('error'), 2000);
            }
        });
    });
}