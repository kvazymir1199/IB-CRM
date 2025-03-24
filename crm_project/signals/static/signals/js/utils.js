// Функция для показа уведомлений
function showNotification(title, message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;

    const icon = document.createElement('i');
    icon.className = `fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} notification-icon`;

    const content = document.createElement('div');
    content.className = 'notification-content';

    const titleElement = document.createElement('div');
    titleElement.className = 'notification-title';
    titleElement.textContent = title;

    const messageElement = document.createElement('div');
    messageElement.className = 'notification-message';
    messageElement.textContent = message;

    content.appendChild(titleElement);
    content.appendChild(messageElement);
    notification.appendChild(icon);
    notification.appendChild(content);

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
} 