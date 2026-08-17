export function updateConnectionStatus(isOnline) {
    const statusEl = document.getElementById('connection-status');
    if (!statusEl) return;

    statusEl.classList.toggle('online', isOnline);
    statusEl.classList.toggle('offline', !isOnline);

    const statusText = statusEl.querySelector('.status-text');
    if (statusText) {
        statusText.textContent = isOnline ? 'Verbunden' : 'Getrennt';
    }
}

export function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;

    const icons = {
        'success': 'check-circle',
        'error': 'alert-circle',
        'warning': 'alert-triangle',
        'info': 'info'
    };

    notification.innerHTML = `
        <i data-lucide="${icons[type] || 'info'}"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(notification);

    if (window.lucide) {
        lucide.createIcons();
    }

    requestAnimationFrame(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    });

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}