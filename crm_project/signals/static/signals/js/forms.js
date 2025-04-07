// Управление формами
const forms = {
    // Отправка формы сигнала
    submitSignalForm: async function (event) {
        event.preventDefault();

        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/signals/api/signals/seasonal/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                showNotification('Success', 'Signal created successfully');
                modal.close();
                window.location.reload();
            } else {
                const error = await response.json();
                showNotification('Error', error.message || 'An error occurred while creating a signal', 'error');
            }
        } catch (error) {
            showNotification('Error', 'An error occurred while sending the form', 'error');
        }
    },

    // Инициализация обработчиков форм
    init: function () {
        const signalForm = document.getElementById('signalForm');
        if (signalForm) {
            signalForm.addEventListener('submit', this.submitSignalForm);
        }
    }
}; 