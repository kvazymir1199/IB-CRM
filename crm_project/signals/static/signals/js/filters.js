// Управление фильтрами
const filters = {
    // Фильтрация сигналов
    filterSignals: function () {
        const searchInput = document.getElementById('searchInput');
        const searchText = searchInput.value.toLowerCase();
        const signalCards = document.querySelectorAll('.signal-card');

        signalCards.forEach(card => {
            const title = card.querySelector('.signal-title').textContent.toLowerCase();
            const description = card.querySelector('.signal-description').textContent.toLowerCase();
            const direction = card.querySelector('.signal-direction').textContent.toLowerCase();

            if (title.includes(searchText) ||
                description.includes(searchText) ||
                direction.includes(searchText)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    },

    // Инициализация фильтров
    init: function () {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.filterSignals);
        }
    }
}; 