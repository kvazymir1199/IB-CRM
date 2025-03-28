"""
Модуль для управления сигналами торгового бота
"""
import sys
from typing import Dict, Any, List
from django.utils import timezone
from django.apps import apps
from trading_bot.models import BotSeasonalSignal, TradeStatus


class BotSignalManager:
    """
    Класс для управления сигналами торгового бота
    """

    def __init__(self):
        """
        Инициализация менеджера сигналов
        """
        print("Начало инициализации BotSignalManager...")
        sys.stdout.flush()

        try:
            print("Получение модели BotSeasonalSignal...")
            sys.stdout.flush()
            self.BotSeasonalSignal = apps.get_model('trading_bot', 'BotSeasonalSignal')
            print("Модель BotSeasonalSignal успешно получена")
            sys.stdout.flush()
        except Exception as e:
            print(f"Ошибка при получении модели BotSeasonalSignal: {str(e)}")
            sys.stdout.flush()
            raise

        print("BotSignalManager успешно инициализирован")
        sys.stdout.flush()

    def check_signals(self) -> None:
        """
        Проверка активных сигналов
        """
        try:
            # Получаем все сигналы, у которых дата выхода больше текущего времени
            signals = self.BotSeasonalSignal.objects.all(
                # exit_date__gt=timezone.now()
            ).select_related('signal', 'signal__symbol')

            signals_info = []
            for signal in signals:
                self._handle_signal(signal)
                signal_info = {
                    'id': signal.id,
                    'symbol': signal.signal.symbol.financial_instrument,
                    'exchange': signal.signal.symbol.exchange,
                    'entry_date': timezone.localtime(signal.entry_date),
                    'exit_date': timezone.localtime(signal.exit_date),
                    'created_at': timezone.localtime(signal.created_at),
                    'updated_at': timezone.localtime(signal.updated_at),
                    'is_active': signal.entry_date <= timezone.now()
                }
                signals_info.append(signal_info)

            if signals_info:
                print(f"\nНайдено активных и будущих сигналов: {len(signals_info)}")
                active_count = sum(1 for s in signals_info if s['is_active'])
                print(f"Найдено {len(signals_info)} сигналов, из них {active_count} активных")
                print(signals_info)
            else:
                print("\nНет сигналов")
            sys.stdout.flush()

        except Exception as e:
            print(f"Ошибка при проверке сигналов: {str(e)}")
            sys.stdout.flush()

    def _handle_signal(self, signal: BotSeasonalSignal):
        if signal.status == TradeStatus.AWAITING:
            print(f"Signal: {signal.pk} awaiting open order")
            if signal.entry_date >= timezone.localtime(timezone.now()):
                print(f"Signal: {signal.pk} ready to open a trade")
                # TODO Make Ib Order connection
                signal.status = TradeStatus.OPEN
