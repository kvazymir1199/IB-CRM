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
                        showNotification('error', 'Ошибка!', 'Не удалось загрузить список символов');
                    }
                } catch (error) {
                    showNotification('error', 'Ошибка!', 'Не удалось загрузить список символов');
                }

                const fields = [
                    { name: 'magic_number', label: 'Magic Number', type: 'number' },
                    {
                        name: 'symbol',
                        label: 'Символ',
                        type: 'select',
                        options: symbols.map(symbol => ({
                            value: symbol.id,
                            label: `${symbol.financial_instrument} - ${symbol.company_name} (${symbol.exchange})`
                        }))
                    },
                    { name: 'entry_month', label: 'Месяц входа', type: 'number', min: 1, max: 12 },
                    { name: 'entry_day', label: 'День входа', type: 'number', min: 1, max: 31 },
                    { name: 'takeprofit_month', label: 'Месяц выхода', type: 'number', min: 1, max: 12 },
                    { name: 'takeprofit_day', label: 'День выхода', type: 'number', min: 1, max: 31 },
                    { name: 'stoploss', label: 'Стоп-лосс', type: 'number', step: '0.01' },
                    { name: 'risk', label: 'Риск (%)', type: 'number', step: '0.01' },
                    {
                        name: 'stoploss_type',
                        label: 'Тип стоп-лосса',
                        type: 'select',
                        options: [
                            { value: 'POINTS', label: 'Пункты' },
                            { value: 'PERCENTAGE', label: 'Проценты' }
                        ]
                    },
                    {
                        name: 'direction',
                        label: 'Направление',
                        type: 'select',
                        options: [
                            { value: 'LONG', label: 'Long' },
                            { value: 'SHORT', label: 'Short' }
                        ]
                    },
                    { name: 'open_time', label: 'Время открытия', type: 'time' },
                    { name: 'close_time', label: 'Время закрытия', type: 'time' }
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
                                emptyOption.textContent = 'Выберите символ';
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
                        showNotification('success', 'Успех!', 'Сигнал успешно создан');
                        modal.style.display = 'none';
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        let errorMessage = responseData.error || responseData.magic_number?.[0] || 'Произошла ошибка при создании сигнала';
                        showNotification('error', 'Ошибка!', errorMessage);
                    }
                } catch (error) {
                    showNotification('error', 'Ошибка!', 'Произошла ошибка при отправке формы');
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
                        showNotification('success', 'Успех!', 'Сигнал успешно обновлен');
                        closeModal();
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        let errorMessage = responseData.error || responseData.magic_number?.[0] || 'Произошла ошибка при обновлении сигнала';
                        showNotification('error', 'Ошибка!', errorMessage);
                    }
                } catch (error) {
                    console.error('Error:', error);
                    showNotification('error', 'Ошибка!', 'Произошла ошибка при отправке данных');
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