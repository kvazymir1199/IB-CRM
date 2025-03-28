from django.db import models
from signals.models import SeasonalSignal


class BotSeasonalSignal(models.Model):
    """
    Модель для хранения информации о торговых сигналах бота.
    Связана с моделью SeasonalSignal.
    """
    signal = models.ForeignKey(
        SeasonalSignal,
        on_delete=models.CASCADE,
        related_name='bot_signals',
        verbose_name='Сезонный сигнал'
    )
    entry_date = models.DateTimeField(
        verbose_name='Дата входа',
        help_text='Дата и время входа в позицию'
    )
    exit_date = models.DateTimeField(
        verbose_name='Дата выхода',
        help_text='Дата и время выхода из позиции'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлен'
    )

    class Meta:
        verbose_name = 'Торговый сигнал'
        verbose_name_plural = 'Торговые сигналы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Торговый сигнал {self.signal} ({self.entry_date.date()})'
