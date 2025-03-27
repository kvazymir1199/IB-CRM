"""
Модуль для управления сигналами торгового бота
"""
import sys
from typing import Dict, Any, List
from django.utils import timezone
from django.apps import apps


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

    def get_active_signals(self) -> List[Dict[str, Any]]:
        """
        Получение активных сигналов

        Returns:
            List[Dict[str, Any]]: Список активных сигналов с информацией
        """
        try:
            current_time = timezone.now()
            print(f"Текущее время: {current_time}")
            sys.stdout.flush()

            # Получаем все сигналы для отладки
            all_signals = self.BotSeasonalSignal.objects.all()
            print(f"Всего сигналов в базе: {all_signals.count()}")
            sys.stdout.flush()

            for signal in all_signals:
                print(f"\nПроверка сигнала ID {signal.id}:")
                print(f"Вход: {signal.entry_date}")
                print(f"Выход: {signal.exit_date}")
                print(f"Текущее время: {current_time}")
                print(f"Вход <= текущее время: {signal.entry_date <= current_time}")
                print(f"Выход > текущее время: {signal.exit_date > current_time}")
                sys.stdout.flush()

            # Получаем активные и будущие сигналы
            signals = self.BotSeasonalSignal.objects.filter(
                exit_date__gt=current_time
            ).select_related('signal', 'signal__symbol')

            print(f"\nНайдено активных и будущих сигналов: {signals.count()}")
            sys.stdout.flush()

            # Формируем информацию о сигналах
            signals_info = []
            for signal in signals:
                signal_info = {
                    'id': signal.id,
                    'symbol': signal.signal.symbol.financial_instrument,
                    'exchange': signal.signal.symbol.exchange,
                    'entry_date': signal.entry_date,
                    'exit_date': signal.exit_date,
                    'created_at': signal.created_at,
                    'updated_at': signal.updated_at,
                    'is_active': signal.entry_date <= current_time
                }
                signals_info.append(signal_info)

            return signals_info

        except Exception as e:
            print(f"Ошибка при получении активных сигналов: {str(e)}")
            sys.stdout.flush()
            return []

    def check_signals(self) -> None:
        """
        Проверка активных сигналов
        """
        try:
            signals = self.get_active_signals()
            if signals:
                active_count = sum(1 for s in signals if s['is_active'])
                print(f"Найдено {len(signals)} сигналов, из них {active_count} активных")
                sys.stdout.flush()
            else:
                print("Нет сигналов")
                sys.stdout.flush()
        except Exception as e:
            print(f"Ошибка при проверке сигналов: {str(e)}")
            sys.stdout.flush()

    def print_active_signals(self) -> None:
        """
        Вывод информации об активных сигналах
        """
        signals = self.get_active_signals()
        
        if not signals:
            print("Нет сигналов")
            sys.stdout.flush()
            return

        print("\nСигналы:")
        print("-" * 50)
        for signal in signals:
            status = "АКТИВНЫЙ" if signal['is_active'] else "БУДУЩИЙ"
            print(f"ID: {signal['id']} ({status})")
            print(f"Символ: {signal['symbol']} ({signal['exchange']})")
            print(f"Вход: {signal['entry_date']}")
            print(f"Выход: {signal['exit_date']}")
            print(f"Создан: {signal['created_at']}")
            print(f"Обновлен: {signal['updated_at']}")
            print("-" * 50)
        sys.stdout.flush()


if __name__ == "__main__":
    # Пример использования
    manager = BotSignalManager()
    manager.print_active_signals() 