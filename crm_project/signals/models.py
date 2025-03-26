from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Direction(models.TextChoices):
    LONG = 'LONG', 'Long'
    SHORT = 'SHORT', 'Short'


class StopLossType(models.TextChoices):
    POINTS = 'POINTS', 'Points'
    PERCENTAGE = 'PERCENTAGE', 'Percentage'


class Symbol(models.Model):
    financial_instrument = models.CharField(max_length=50, unique=True)
    company_name = models.CharField(max_length=100)
    exchange = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.financial_instrument} ({self.exchange})"

    class Meta:
        ordering = ['financial_instrument']
        verbose_name = 'Символ'
        verbose_name_plural = 'Символы'


class Signal(models.Model):
    magic_number = models.IntegerField(
        unique=True,
        error_messages={
            'unique': 'Сигнал с таким Magic Number уже существует'
        }
    )
    symbol = models.ForeignKey(
        Symbol,
        on_delete=models.PROTECT,
        verbose_name='Символ'
    )
    stoploss = models.DecimalField(max_digits=10, decimal_places=2)
    stoploss_type = models.CharField(
        max_length=10,
        choices=StopLossType.choices,
        default=StopLossType.POINTS
    )
    risk = models.DecimalField(max_digits=5, decimal_places=2)
    direction = models.CharField(
        max_length=5,
        choices=Direction.choices,
        default=Direction.LONG
    )

    def __str__(self):
        return f"{self.symbol} - {self.direction} (Magic: {self.magic_number})"

    class Meta:
        abstract = True
        ordering = ['-id']


class SeasonalSignal(Signal):
    entry_month = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12)
        ]
    )
    entry_day = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(31)
        ]
    )
    takeprofit_month = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12)
        ]
    )
    takeprofit_day = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(31)
        ]
    )
    open_time = models.TimeField()
    close_time = models.TimeField()

    class Meta(Signal.Meta):
        abstract = False

    def __str__(self):
        return f"{super().__str__()} - Entry: {self.entry_month}/{self.entry_day} TP: {self.takeprofit_month}/{self.takeprofit_day}"