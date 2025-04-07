from django.db import models
from signals.models import SeasonalSignal


class TradeStatus(models.TextChoices):
    AWAITING = "awaiting", "Awaiting"
    OPEN = "open", "Trade Open"
    CLOSE = "close", "Trade Close"


class BotSeasonalSignal(models.Model):
    """
    Модель для хранения информации о торговых сигналах бота.
    Связана с моделью SeasonalSignal.
    """
    signal = models.ForeignKey(
        SeasonalSignal,
        on_delete=models.CASCADE,
        related_name='bot_signals',
        verbose_name='Seasonal signal'
    )
    entry_date = models.DateTimeField(
        verbose_name='Entry date',
        help_text='Date and time of entry into the position'
    )
    exit_date = models.DateTimeField(
        verbose_name='Exit date',
        help_text='Date and time of exit from the position'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated'
    )
    status = models.CharField(
        max_length=10,  # Максимальная длина строки
        choices=TradeStatus.choices,
        default=TradeStatus.AWAITING,
    )
    order_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Order ID',
        help_text='Order ID in Interactive Brokers'
    )
    stop_order_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Stop order ID',
        help_text='Stop order ID in Interactive Brokers'
    )
    
    class Meta:
        verbose_name = 'Trading signal'
        verbose_name_plural = 'Trading signals'
        ordering = ['-created_at']

    def __str__(self):
        return f'Trading signal {self.signal} ({self.entry_date.date()})'


class BotState(models.Model):
    """Модель для хранения состояния бота"""
    is_running = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bot state'
        verbose_name_plural = 'Bot state'
    
    def __str__(self):
        return f"Bot {'running' if self.is_running else 'stopped'}"
    
    @classmethod
    def get_state(cls):
        """Получить текущее состояние бота"""
        state, created = cls.objects.get_or_create(id=1)
        return state
