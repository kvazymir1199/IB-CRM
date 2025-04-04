#!/bin/bash
echo "Запускаем Docker Compose с Unix-скриптом..."

# Редактируем docker-compose.yml для использования Unix-команды
sed -i 's/# command: bash .\/entrypoint.sh/command: bash .\/entrypoint.sh/g' docker-compose.yml
sed -i 's/command: cmd \/c entrypoint_win.bat/# command: cmd \/c entrypoint_win.bat/g' docker-compose.yml

# Запускаем Docker Compose
docker-compose up -d --build

echo "Docker Compose запущен с Unix-настройками." 