import os
import django
from trading_bot import TradingBot

# Инициализация Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

def main():
    """
    Основная функция для запуска торгового бота
    """
    bot = TradingBot()
    try:
        # Проверяем сигналы
        bot.check_signals()
    finally:
        # Закрываем соединение
        bot.disconnect()

if __name__ == '__main__':
    main() 