#!/bin/bash

set -e

# Создаем необходимые директории
mkdir -p /app/static
mkdir -p /app/logs

echo "Waiting for 5 seconds to let the database service start..."
sleep 5

# Удаляем все миграции, если они существуют
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# Создаем миграции в правильном порядке
echo "Creating migrations for signals app..."
python manage.py makemigrations signals

echo "Creating migrations for trading_bot app..."
python manage.py makemigrations trading_bot

# Применяем миграции
echo "Applying migrations..."
python manage.py migrate

# Запускаем сервер Django
echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000 