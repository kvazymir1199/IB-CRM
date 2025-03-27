from django.core.management.base import BaseCommand
from trading_bot.core.bot import TradingBot
import time

class Command(BaseCommand):
    help = 'Запускает торгового бота'

    def handle(self, *args, **options):
        self.stdout.write('Запуск торгового бота...')
        
        bot = TradingBot()
        
        try:
            while True:
                results = bot.check_signals()
                self.stdout.write(f'Результаты проверки сигналов: {results}')
                time.sleep(60)  # Проверка каждую минуту
                
        except KeyboardInterrupt:
            self.stdout.write('Остановка бота...')
        finally:
            bot.disconnect() 