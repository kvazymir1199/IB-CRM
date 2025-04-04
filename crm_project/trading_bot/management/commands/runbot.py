from django.core.management.base import BaseCommand
from trading_bot.bot import TradingBot


class Command(BaseCommand):
    help = 'Запускает торгового бота'

    def handle(self, *args, **options):
        self.stdout.write('Запуск торгового бота...')
        
        bot = TradingBot()

        bot.run()

                
