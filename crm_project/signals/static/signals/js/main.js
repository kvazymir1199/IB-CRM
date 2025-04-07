document.addEventListener('DOMContentLoaded', function () {
    // Функция для показа уведомлений
    window.showNotification = function (type, title, message) {
        // Удаляем предыдущие уведомления
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => {
            notification.remove();
        });

        // Создаем новое уведомление
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;

        const icon = type === 'error' ? '⚠️' : '✅';

        notification.innerHTML = `
            <div class="notification-icon">${icon}</div>
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <div class="notification-close">✕</div>
        `;

        document.body.appendChild(notification);

        // Обработчик закрытия
        const closeNotification = () => {
            notification.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => {
                notification.remove();
            }, 300);
        };

        // Закрытие по клику на крестик
        notification.querySelector('.notification-close').addEventListener('click', closeNotification);

        // Автоматическое закрытие через 5 секунд
        setTimeout(closeNotification, 5000);
    };

    // Инициализация формы создания сигнала
    const initCreateForm = () => {
        const modal = document.getElementById('signalModal');
        const addSignalBtn = document.getElementById('addSignalBtn');
        const closeBtn = modal?.querySelector('.close');
        const signalForm = document.getElementById('signalForm');
        const seasonalSignalFields = document.getElementById('seasonalSignalFields');

        if (addSignalBtn && modal && signalForm && seasonalSignalFields) {
            // Открытие модального окна
            addSignalBtn.addEventListener('click', function () {
                modal.style.display = 'block';
                createSeasonalSignalForm();
            });

            // Закрытие модального окна
            if (closeBtn) {
                closeBtn.addEventListener('click', function () {
                    modal.style.display = 'none';
                });
            }

            // Закрытие при клике вне модального окна
            window.addEventListener('click', function (event) {
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            });

            // Создание формы для сезонного сигнала
            async function createSeasonalSignalForm() {
                // Загружаем список символов
                let symbols = [];
                try {
                    const response = await fetch('/api/signals/symbols/');
                    if (response.ok) {
                        symbols = await response.json();
                    } else {
                        showNotification('error', 'Error!', 'Failed to load symbol list');
                    }
                } catch (error) {
                    showNotification('error', 'Error!', 'Failed to load symbol list');
                }

                const fields = [
                    { name: 'magic_number', label: 'Magic Number', type: 'number' },
                    {
                        name: 'symbol',
                        label: 'Symbol',
                        type: 'select',
                        options: symbols.map(symbol => ({
                            value: symbol.id,
                            label: `${symbol.financial_instrument} - ${symbol.company_name} (${symbol.exchange})`
                        }))
                    },
                    {
                        name: 'entry_month',
                        label: 'Month of entry',
                        type: 'select',
                        options: [
                            { value: 1, label: 'January' },
                            { value: 2, label: 'February' },
                            { value: 3, label: 'March' },
                            { value: 4, label: 'April' },
                            { value: 5, label: 'May' },
                            { value: 6, label: 'June' },
                            { value: 7, label: 'July' },
                            { value: 8, label: 'August' },
                            { value: 9, label: 'September' },
                            { value: 10, label: 'October' },
                            { value: 11, label: 'November' },
                            { value: 12, label: 'December' }
                        ]
                    },
                    { name: 'entry_day', label: 'Day of entry', type: 'number', min: 1, max: 31 },
                    {
                        name: 'takeprofit_month',
                        label: 'Month of exit',
                        type: 'select',
                        options: [
                            { value: 1, label: 'January' },
                            { value: 2, label: 'February' },
                            { value: 3, label: 'March' },
                            { value: 4, label: 'April' },
                            { value: 5, label: 'May' },
                            { value: 6, label: 'June' },
                            { value: 7, label: 'July' },
                            { value: 8, label: 'August' },
                            { value: 9, label: 'September' },
                            { value: 10, label: 'October' },
                            { value: 11, label: 'November' },
                            { value: 12, label: 'December' }
                        ]
                    },
                    { name: 'takeprofit_day', label: 'Day of exit', type: 'number', min: 1, max: 31 },
                    { name: 'stoploss', label: 'Stop loss', type: 'number', step: '0.01' },
                    { name: 'risk', label: 'Risk (%)', type: 'number', step: '0.01' },
                    {
                        name: 'stoploss_type',
                        label: 'Stop loss type',
                        type: 'select',
                        options: [
                            { value: 'POINTS', label: 'Points' },
                            { value: 'PERCENTAGE', label: 'Percentage' }
                        ]
                    },
                    {
                        name: 'direction',
                        label: 'Direction',
                        type: 'select',
                        options: [
                            { value: 'LONG', label: 'Long' },
                            { value: 'SHORT', label: 'Short' }
                        ]
                    },
                    { name: 'open_time', label: 'Open time', type: 'time' },
                    { name: 'close_time', label: 'Close time', type: 'time' }
                ];

                seasonalSignalFields.innerHTML = '';
                fields.forEach(field => {
                    const formGroup = document.createElement('div');
                    formGroup.className = 'form-group';

                    const label = document.createElement('label');
                    label.textContent = field.label;
                    label.htmlFor = field.name;

                    let input;
                    if (field.type === 'select') {
                        input = document.createElement('select');
                        if (field.options) {
                            // Добавляем пустой option для select символа
                            if (field.name === 'symbol') {
                                const emptyOption = document.createElement('option');
                                emptyOption.value = '';
                                emptyOption.textContent = 'Select symbol';
                                input.appendChild(emptyOption);
                            }
                            field.options.forEach(option => {
                                const optionElement = document.createElement('option');
                                optionElement.value = option.value;
                                optionElement.textContent = option.label;
                                input.appendChild(optionElement);
                            });
                        }
                    } else {
                        input = document.createElement('input');
                        input.type = field.type;
                        if (field.min !== undefined) input.min = field.min;
                        if (field.max !== undefined) input.max = field.max;
                        if (field.step !== undefined) input.step = field.step;
                    }

                    input.name = field.name;
                    input.id = field.name;
                    input.className = 'form-control';
                    input.required = true;

                    formGroup.appendChild(label);
                    formGroup.appendChild(input);
                    seasonalSignalFields.appendChild(formGroup);
                });
            }

            // Обработка отправки формы создания
            signalForm.addEventListener('submit', async function (e) {
                e.preventDefault();
                const formData = new FormData(signalForm);
                const data = {};

                for (let [key, value] of formData.entries()) {
                    if (key !== 'csrfmiddlewaretoken') {
                        if (key === 'magic_number' ||
                            key === 'entry_month' || key === 'entry_day' ||
                            key === 'takeprofit_month' || key === 'takeprofit_day') {
                            data[key] = parseInt(value);
                        } else if (key === 'stoploss' || key === 'risk') {
                            data[key] = parseFloat(value);
                        } else {
                            data[key] = value;
                        }
                    }
                }

                try {
                    const response = await fetch('/api/signals/seasonal/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });

                    const responseData = await response.json();

                    if (response.ok) {
                        showNotification('success', 'Success!', 'Signal created successfully');
                        modal.style.display = 'none';
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        let errorMessage = responseData.error || responseData.magic_number?.[0] || 'An error occurred while creating a signal';
                        showNotification('error', 'Error!', errorMessage);
                    }
                } catch (error) {
                    showNotification('error', 'Error!', 'An error occurred while sending the form');
                }
            });
        }
    };

    // Инициализация формы редактирования
    const initEditForm = () => {
        const editModal = document.getElementById('editModal');
        const editBtn = document.getElementById('editSignalBtn');
        const editForm = document.getElementById('editSignalForm');
        const closeButtons = document.querySelectorAll('.close, #cancelEditBtn');

        if (editBtn && editModal && editForm) {
            // Открытие модального окна
            editBtn.addEventListener('click', function () {
                editModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            });

            // Закрытие модального окна
            function closeModal() {
                editModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }

            // Закрытие по кнопкам
            closeButtons.forEach(button => {
                if (button) {
                    button.addEventListener('click', closeModal);
                }
            });

            // Закрытие при клике вне модального окна
            window.addEventListener('click', function (event) {
                if (event.target === editModal) {
                    closeModal();
                }
            });

            // Обработка отправки формы редактирования
            editForm.addEventListener('submit', async function (e) {
                e.preventDefault();
                const formData = new FormData(editForm);
                const data = {};

                for (let [key, value] of formData.entries()) {
                    if (key !== 'csrfmiddlewaretoken') {
                        if (key === 'magic_number' ||
                            key === 'entry_month' || key === 'entry_day' ||
                            key === 'takeprofit_month' || key === 'takeprofit_day') {
                            data[key] = parseInt(value);
                        } else if (key === 'stoploss' || key === 'risk') {
                            data[key] = parseFloat(value);
                        } else {
                            data[key] = value;
                        }
                    }
                }

                try {
                    const signalId = editForm.dataset.signalId;
                    console.log('Updating signal with ID:', signalId);
                    console.log('Request URL:', `/api/signals/seasonal/${signalId}/`);
                    console.log('Request data:', data);

                    const response = await fetch(`/api/signals/seasonal/${signalId}/`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                        },
                        body: JSON.stringify(data)
                    });

                    console.log('Response status:', response.status);
                    const responseData = await response.json();
                    console.log('Response data:', responseData);

                    if (response.ok) {
                        showNotification('success', 'Success!', 'Signal updated successfully');
                        closeModal();
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        let errorMessage = responseData.error || responseData.magic_number?.[0] || 'An error occurred while updating the signal';
                        showNotification('error', 'Error!', errorMessage);
                    }
                } catch (error) {
                    console.error('Error:', error);
                    showNotification('error', 'Error!', 'An error occurred while sending data');
                }
            });
        }
    };

    // Инициализация всех форм
    initCreateForm();
    initEditForm();

    // Функция для форматирования даты и времени
    function formatDateTime(date) {
        return date.toISOString().slice(0, 16);
    }

    // Заполнение формы текущими данными
    const editForm = document.getElementById('editSignalForm');
    if (editForm) {
        const signalData = window.signalData;
        if (signalData) {
            Object.keys(signalData).forEach(key => {
                const input = editForm.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'datetime-local') {
                        // Преобразуем строку даты в объект Date и форматируем
                        const date = new Date(signalData[key]);
                        input.value = formatDateTime(date);
                    } else {
                        input.value = signalData[key];
                    }
                }
            });
        }
    }
}); 