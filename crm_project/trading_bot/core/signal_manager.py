import logging
from django.utils import timezone
from signals.models import SeasonalSignal
from ..models import BotSeasonalSignal

logger = logging.getLogger(__name__)


class SignalManager:
    """
    Класс для управления торговыми сигналами.
    Проверяет наличие сигналов и создает BotSeasonalSignal при необходимости.
    """
    
    def check_signals(self):
        """
        Проверка всех сигналов и создание BotSeasonalSignal при необходимости.
        
        Returns:
            int: Количество созданных сигналов
        """
        created_count = 0
        current_year = timezone.now().year
        current_time = timezone.now()
        
        logger.info(f"Начало проверки сигналов. Текущее время: {current_time}")
        
        # Получаем все сезонные сигналы
        seasonal_signals = SeasonalSignal.objects.all()
        logger.info(f"Найдено сезонных сигналов: {seasonal_signals.count()}")
        
        for signal in seasonal_signals:
            try:
                logger.info(
                    f"Обработка сигнала: {signal} "
                    f"(Magic: {signal.magic_number})"
                )
                if self._process_signal(signal, current_year):
                    created_count += 1
            except Exception as e:
                logger.error(f"Ошибка обработки сигнала {signal}: {e}")
        
        logger.info(f"Проверка сигналов завершена. Создано: {created_count}")
        return created_count
    
    def _process_signal(
        self, signal: SeasonalSignal, current_year: int
    ) -> bool:
        """
        Обработка отдельного сигнала
        
        Args:
            signal: Сезонный сигнал для обработки
            current_year: Текущий год
            
        Returns:
            bool: True если был создан новый сигнал, False в противном случае
        """
        # Проверяем существование BotSeasonalSignal для текущего года
        existing_bot_signal = BotSeasonalSignal.objects.filter(
            signal=signal,
            created_at__year=current_year
        ).exists()
        
        if existing_bot_signal:
            logger.info(
                f"Сигнал {signal} уже существует для года {current_year}"
            )
            return False
        
        # Создаем дату входа из компонентов сигнала
        entry_date = timezone.make_aware(timezone.datetime(
            year=current_year,
            month=signal.entry_month,
            day=signal.entry_day,
            hour=signal.open_time.hour,
            minute=signal.open_time.minute
        ))
        
        current_time = timezone.now()
        logger.info(
            f"Сравнение дат для сигнала {signal}:\n"
            f"Дата входа: {entry_date}\n"
            f"Текущее время: {current_time}\n"
            f"Вход в будущем: {entry_date > current_time}"
        )
        
        # Если дата входа в будущем, создаем сигнал
        if entry_date > current_time:
            self._create_bot_signal(signal, current_year)
            return True
            
        logger.info(
            f"Сигнал {signal} не создан, так как дата входа "
            f"({entry_date}) в прошлом"
        )
        return False
    
    def _create_bot_signal(
        self, signal: SeasonalSignal, current_year: int
    ):
        """
        Создание торгового сигнала
        
        Args:
            signal: Сезонный сигнал, на основе которого создается 
                   BotSeasonalSignal
            current_year: Текущий год
        """
        # Создаем даты входа и выхода для текущего года
        entry_date = timezone.make_aware(timezone.datetime(
            year=current_year,
            month=signal.entry_month,
            day=signal.entry_day,
            hour=signal.open_time.hour,
            minute=signal.open_time.minute
        ))
        
        exit_date = timezone.make_aware(timezone.datetime(
            year=current_year,
            month=signal.takeprofit_month,
            day=signal.takeprofit_day,
            hour=signal.close_time.hour,
            minute=signal.close_time.minute
        ))
        
        # Если дата выхода меньше даты входа, значит выход в следующем году
        if exit_date < entry_date:
            exit_date = timezone.make_aware(timezone.datetime(
                year=current_year + 1,
                month=signal.takeprofit_month,
                day=signal.takeprofit_day,
                hour=signal.close_time.hour,
                minute=signal.close_time.minute
            ))
            logger.info(
                f"Дата выхода перенесена на следующий год: {exit_date}"
            )
        
        bot_signal = BotSeasonalSignal.objects.create(
            signal=signal,
            entry_date=entry_date,
            exit_date=exit_date
        )
        
        logger.info(
            f"Создан торговый сигнал {bot_signal}:\n"
            f"Вход: {entry_date}\n"
            f"Выход: {exit_date}\n"
            f"Magic: {signal.magic_number}"
        )


# Создаем глобальный экземпляр менеджера
signal_manager = SignalManager() 
