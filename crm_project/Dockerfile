# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код проекта
COPY . .

# Создаем пользователя без прав root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Запускаем команду по умолчанию
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 