export function initUtils() {
    // Momentan nichts zu initialisieren
}

export function updateConnectionStatus(isOnline) {
    const statusEl = document.getElementById('connection-status');
    if (!statusEl) return;

    statusEl.classList.toggle('online', isOnline);
    statusEl.classList.toggle('offline', !isOnline);

    const statusText = statusEl.querySelector('.status-text');
    if (statusText) {
        statusText.textContent = isOnline ? 'Verbunden' : 'Getrennt';
    }

    // Add pulse animation when connecting
    if (isOnline) {
        statusEl.classList.add('pulse');
        setTimeout(() => statusEl.classList.remove('pulse'), 2000);
    }
}

export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Zentrale Notification-Funktion (statt Duplikate in devices.js und settings.js)
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

    // Update lucide icons if available
    if (window.lucide) {
        lucide.createIcons();
    }

    // Fade in
    requestAnimationFrame(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    });

    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}