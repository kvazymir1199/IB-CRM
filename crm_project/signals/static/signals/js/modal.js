// Управление модальными окнами
const modal = {
    // Открытие модального окна
    open: function () {
        const modal = document.getElementById('signalModal');
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    },

    // Закрытие модального окна
    close: function () {
        const modal = document.getElementById('signalModal');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';

        // Очищаем форму при закрытии
        const form = document.getElementById('signalForm');
        if (form) form.reset();
    },

    // Инициализация обработчиков событий
    init: function () {
        const modal = document.getElementById('signalModal');
        const closeButtons = modal.querySelectorAll('.close, .close-btn');

        // Закрытие по клику на крестик или кнопку отмены
        closeButtons.forEach(btn => {
            btn.onclick = () => this.close();
        });

        // Закрытие по клику вне модального окна
        window.onclick = (event) => {
            if (event.target === modal) {
                this.close();
            }
        };

        // Переключение типа сигнала
        const typeButtons = document.querySelectorAll('.signal-type-btn');
        typeButtons.forEach(button => {
            button.addEventListener('click', () => {
                typeButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                const type = button.dataset.type;
                this.switchSignalType(type);
            });
        });

        // Предотвращаем закрытие при клике на контент
        const modalContent = modal.querySelector('.modal-content');
        modalContent.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    },

    // Переключение типа сигнала
    switchSignalType: function (type) {
        const seasonalFields = document.getElementById('seasonalSignalFields');
        if (type === 'seasonal') {
            const fields = [
                { name: 'magic_number', label: 'Magic Number', type: 'number' },
                { name: 'symbol', label: 'Symbol', type: 'text' },
                { name: 'month', label: 'Month', type: 'number', min: 1, max: 12 },
                { name: 'entry_month', label: 'Month of entry', type: 'number', min: 1, max: 12 },
                { name: 'entry_day', label: 'Day of entry', type: 'number', min: 1, max: 31 },
                { name: 'takeprofit_month', label: 'Month of exit', type: 'number', min: 1, max: 12 },
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

            seasonalFields.innerHTML = '';
            fields.forEach(field => {
                const formGroup = document.createElement('div');
                formGroup.className = 'form-group';

                const label = document.createElement('label');
                label.textContent = field.label;
                label.htmlFor = field.name;

                let input;
                if (field.type === 'select') {
                    input = document.createElement('select');
                    field.options.forEach(option => {
                        const optionElement = document.createElement('option');
                        optionElement.value = option.value;
                        optionElement.textContent = option.label;
                        input.appendChild(optionElement);
                    });
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
                seasonalFields.appendChild(formGroup);
            });
        }
    }
}; 