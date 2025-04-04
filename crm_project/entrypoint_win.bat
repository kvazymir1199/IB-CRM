@echo off
SETLOCAL

REM Создаем необходимые директории
mkdir -p /app/static
mkdir -p /app/logs

echo Waiting for 5 seconds to let the database service start...
timeout /t 5

REM Удаляем все файлы миграций, кроме __init__.py
for /r %%i in (*/migrations/*.py) do (
    echo %%~nxi | findstr /v "__init__.py" > nul && del "%%i"
)
for /r %%i in (*/migrations/*.pyc) do del "%%i"

REM Создаем миграции в правильном порядке
echo Creating migrations for signals app...
python manage.py makemigrations signals

echo Creating migrations for trading_bot app...
python manage.py makemigrations trading_bot

REM Применяем миграции
echo Applying migrations...
python manage.py migrate

REM Запускаем сервер Django
echo Starting Django server...
python manage.py runserver 0.0.0.0:8000 