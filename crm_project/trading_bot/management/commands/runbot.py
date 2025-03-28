from django.core.management.base import BaseCommand
from trading_bot.core.bot import TradingBot
import time

class Command(BaseCommand):
    help = 'Запускает торгового бота'

    def handle(self, *args, **options):
        self.stdout.write('Запуск торгового бота...')
        
        bot = TradingBot()

        bot.run()

                
