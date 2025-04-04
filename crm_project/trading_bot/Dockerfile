FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Установка пакета в режиме разработки
RUN pip install -e .

# Переменные окружения
ENV IB_HOST=host.docker.internal
ENV IB_PORT=4002
ENV IB_CLIENT_ID=123

# Запуск бота
CMD ["python", "manage.py", "runbot"] 