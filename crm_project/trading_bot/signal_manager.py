"""
Модуль для обработки торговых сигналов
"""

import logging
from django.utils import timezone
import pytz
from signals.models import SeasonalSignal
from trading_bot.models import BotSeasonalSignal
from datetime import datetime

logger = logging.getLogger(__name__)


class SignalManager:
    """
    Класс для обработки торговых сигналов
    """

    def __init__(self):
        # Получаем локальную временную зону из настроек Django
        self.local_tz = pytz.timezone(timezone.get_current_timezone_name())
        
        # Логируем информацию о часовом поясе при инициализации
        logger.info(
            f"Инициализация SignalManager с часовым поясом: "
            f"{self.local_tz.zone} (сейчас: UTC{datetime.now(self.local_tz).strftime('%z')})"
        )

    def check_signals(self):
        """
        Проверка всех сигналов, создание новых и обновление существующих
        BotSeasonalSignal.

        Returns:
            tuple: (int, int) - (количество созданных сигналов,
                                количество обновленных)
        """
        created_count = 0
        updated_count = 0
        current_year = timezone.now().year
        current_time = timezone.now()

        logger.info(f"Начало проверки сигналов. Текущее время: {current_time}")

        # Получаем все сезонные сигналы
        seasonal_signals = SeasonalSignal.objects.all()
        logger.info(f"Найдено сезонных сигналов: {seasonal_signals.count()}")

        for signal in seasonal_signals:
            try:
                logger.info(
                    f"Обработка сигнала: {signal} " f"(Magic: {signal.magic_number})"
                )

                # Проверяем существующие сигналы
                existing_signals = BotSeasonalSignal.objects.filter(
                    signal=signal, entry_date__gt=current_time
                )

                if existing_signals.exists():
                    # Обновляем существующие сигналы
                    updated = self.update_bot_signals(signal)
                    updated_count += updated
                    logger.info(f"Обновлено {updated} сигналов для {signal}")
                else:
                    # Создаем новый сигнал
                    if self._process_signal(signal, current_year):
                        created_count += 1

            except Exception as e:
                logger.error(f"Ошибка обработки сигнала {signal}: {e}")

        logger.info(
            f"Проверка сигналов завершена. "
            f"Создано: {created_count}, Обновлено: {updated_count}"
        )
        return created_count, updated_count

    def update_bot_signals(self, seasonal_signal: SeasonalSignal) -> int:
        """
        Обновляет все связанные BotSeasonalSignal при изменении
        SeasonalSignal.

        Args:
            seasonal_signal: Измененный сезонный сигнал

        Returns:
            int: Количество обновленных сигналов
        """
        updated_count = 0
        current_time = timezone.now()

        logger.info(f"Начало обновления BotSeasonalSignal для {seasonal_signal}")

        # Получаем все связанные BotSeasonalSignal
        bot_signals = BotSeasonalSignal.objects.filter(
            signal=seasonal_signal,
            entry_date__gt=current_time,  # Только будущие сигналы
        )

        for bot_signal in bot_signals:
            try:
                # Создаем новые даты в фиксированном часовом поясе UTC+1
                entry_date = self.create_date_with_fixed_timezone(
                    year=bot_signal.entry_date.year,
                    month=seasonal_signal.entry_month,
                    day=seasonal_signal.entry_day,
                    hour=seasonal_signal.open_time.hour,
                    minute=seasonal_signal.open_time.minute
                )

                exit_date = self.create_date_with_fixed_timezone(
                    year=bot_signal.exit_date.year,
                    month=seasonal_signal.takeprofit_month,
                    day=seasonal_signal.takeprofit_day,
                    hour=seasonal_signal.close_time.hour,
                    minute=seasonal_signal.close_time.minute
                )

                # Проверяем, нужно ли перенести дату выхода на следующий год
                if exit_date < entry_date:
                    exit_date = self.create_date_with_fixed_timezone(
                        year=bot_signal.exit_date.year + 1,
                        month=seasonal_signal.takeprofit_month,
                        day=seasonal_signal.takeprofit_day,
                        hour=seasonal_signal.close_time.hour,
                        minute=seasonal_signal.close_time.minute
                    )

                # Обновляем даты только если они изменились
                if (
                    bot_signal.entry_date != entry_date
                    or bot_signal.exit_date != exit_date
                ):
                    bot_signal.entry_date = entry_date
                    bot_signal.exit_date = exit_date
                    bot_signal.save()

                    logger.info(
                        f"Обновлен BotSeasonalSignal {bot_signal}:\n"
                        f"Новая дата входа (UTC+1): {entry_date}\n"
                        f"Новая дата выхода (UTC+1): {exit_date}"
                    )
                    updated_count += 1

            except Exception as e:
                logger.error(f"Ошибка обновления BotSeasonalSignal {bot_signal}: {e}")

        logger.info(
            f"Обновление BotSeasonalSignal завершено. "
            f"Обновлено сигналов: {updated_count}"
        )
        return updated_count

    def _process_signal(self, signal: SeasonalSignal, current_year: int) -> bool:
        """
        Обработка отдельного сигнала

        Args:
            signal: Сезонный сигнал для обработки
            current_year: Текущий год

        Returns:
            bool: True если был создан новый сигнал, False в противном случае
        """
        # Проверяем существование BotSeasonalSignal для текущего года и magic_number
        existing_bot_signal = BotSeasonalSignal.objects.filter(
            signal=signal,
            signal__magic_number=signal.magic_number,  # Добавляем фильтр по magic_number
            created_at__year=current_year,
        ).exists()

        if existing_bot_signal:
            logger.info(
                f"Сигнал {signal} (Magic: {signal.magic_number}) уже существует для года {current_year}"
            )
            return False

        # Получаем текущее время (UTC)
        current_time = timezone.now()
        
        # Логируем параметры сигнала для диагностики
        logger.info(
            f"Параметры сигнала {signal.id} (Magic: {signal.magic_number}):\n"
            f"Месяц входа: {signal.entry_month}\n"
            f"День входа: {signal.entry_day}\n"
            f"Время открытия: {signal.open_time}\n"
            f"Текущее время сервера (UTC): {current_time}\n"
            f"Текущий год: {current_year}"
        )

        # Создаем дату входа в фиксированном часовом поясе UTC+1
        entry_date = self.create_date_with_fixed_timezone(
            year=current_year,
            month=signal.entry_month,
            day=signal.entry_day,
            hour=signal.open_time.hour,
            minute=signal.open_time.minute
        )

        # Преобразуем время в UTC для правильного сравнения
        entry_date_utc = entry_date.astimezone(pytz.UTC)

        logger.info(
            f"Сравнение дат для сигнала {signal} (Magic: {signal.magic_number}):\n"
            f"Дата входа (Fixed UTC+1): {entry_date}\n"
            f"Дата входа (UTC): {entry_date_utc}\n"
            f"Текущее время (UTC): {current_time}\n"
            f"Разница (минуты): {(entry_date_utc - current_time).total_seconds() / 60:.2f}\n"
            f"Вход в будущем: {entry_date_utc > current_time}"
        )

        # Сравниваем даты в одинаковом часовом поясе (UTC)
        if entry_date_utc > current_time:
            self._create_bot_signal(signal, current_year)
            return True
        
        # Проверяем, находится ли время входа в пределах 5 минут от текущего
        # Это поможет в ситуациях, когда время почти совпадает
        time_diff_minutes = (current_time - entry_date_utc).total_seconds() / 60
        if 0 < time_diff_minutes < 5:
            logger.warning(
                f"Сигнал {signal} (Magic: {signal.magic_number}) пропущен из-за небольшой разницы во времени.\n"
                f"Разница всего {time_diff_minutes:.2f} минут. Возможно, нужно обновить время в базе данных."
            )

        logger.info(
            f"Сигнал {signal} (Magic: {signal.magic_number}) не создан, так как дата входа "
            f"({entry_date}) в прошлом"
        )
        return False

    def _create_bot_signal(self, signal: SeasonalSignal, current_year: int):
        """
        Создание торгового сигнала

        Args:
            signal: Сезонный сигнал, на основе которого создается
                   BotSeasonalSignal
            current_year: Текущий год
        """
        # Создаем даты входа и выхода в фиксированном часовом поясе UTC+1
        entry_date = self.create_date_with_fixed_timezone(
            year=current_year,
            month=signal.entry_month,
            day=signal.entry_day,
            hour=signal.open_time.hour,
            minute=signal.open_time.minute
        )

        exit_date = self.create_date_with_fixed_timezone(
            year=current_year,
            month=signal.takeprofit_month,
            day=signal.takeprofit_day,
            hour=signal.close_time.hour,
            minute=signal.close_time.minute
        )

        # Если дата выхода меньше даты входа, значит выход в следующем году
        if exit_date < entry_date:
            exit_date = self.create_date_with_fixed_timezone(
                year=current_year + 1,
                month=signal.takeprofit_month,
                day=signal.takeprofit_day,
                hour=signal.close_time.hour,
                minute=signal.close_time.minute
            )
            logger.info(f"Дата выхода перенесена на следующий год: {exit_date}")

        bot_signal = BotSeasonalSignal.objects.create(
            signal=signal, entry_date=entry_date, exit_date=exit_date
        )

        logger.info(
            f"Создан торговый сигнал {bot_signal}:\n"
            f"Вход (UTC+1): {entry_date}\n"
            f"Выход (UTC+1): {exit_date}\n"
            f"Magic: {signal.magic_number}"
        )

    def create_date_with_fixed_timezone(self, year, month, day, hour, minute, 
                                        fixed_timezone='Etc/GMT-1'):
        """
        Создает дату с указанием часового пояса UTC+1 (без учета DST)
        
        Args:
            year: Год
            month: Месяц
            day: День
            hour: Час
            minute: Минута
            fixed_timezone: Фиксированный часовой пояс (по умолчанию UTC+1)
            
        Returns:
            datetime: Дата в указанном часовом поясе
        """
        # Создаем дату в указанном часовом поясе (UTC+1)
        fixed_tz = pytz.timezone(fixed_timezone)
        date_in_fixed_tz = fixed_tz.localize(
            timezone.datetime(year, month, day, hour, minute)
        )
        
        logger.info(
            f"Создана дата в фиксированном часовом поясе {fixed_timezone}: "
            f"{date_in_fixed_tz}"
        )
        
        return date_in_fixed_tz


# Создаем глобальный экземпляр менеджера
signal_manager = SignalManager()
