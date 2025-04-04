"""
Команда для проверки и создания сигналов
"""
from django.core.management.base import BaseCommand
from trading_bot.signal_manager import signal_manager


class Command(BaseCommand):
    help = 'Проверяет и создает BotSeasonalSignal при необходимости'

    def handle(self, *args, **options):
        self.stdout.write('Начинаю проверку сигналов...')
        created_count = signal_manager.check_signals()
        self.stdout.write(
            self.style.SUCCESS(
                f'Проверка завершена. Создано сигналов: {created_count}'
            )
        ) 