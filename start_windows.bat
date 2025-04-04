@echo off
echo Запускаем Docker Compose с Windows-скриптом...

REM Редактируем docker-compose.yml для использования Windows-команды
powershell -Command "(Get-Content docker-compose.yml) -replace 'command: bash ./entrypoint.sh', '# command: bash ./entrypoint.sh' | Out-File -encoding ASCII docker-compose.yml.tmp"
powershell -Command "(Get-Content docker-compose.yml.tmp) -replace '# command: cmd /c entrypoint_win.bat', 'command: cmd /c entrypoint_win.bat' | Out-File -encoding ASCII docker-compose.yml"
del docker-compose.yml.tmp

REM Запускаем Docker Compose
docker-compose up -d --build

echo Docker Compose запущен с Windows-настройками.
pause 