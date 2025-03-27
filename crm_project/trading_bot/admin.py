"""
Административный интерфейс для торгового бота
"""
from django.contrib import admin
from .models import BotSeasonalSignal


@admin.register(BotSeasonalSignal)
class BotSeasonalSignalAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для BotSeasonalSignal
    """
    list_display = (
        'signal',
        'entry_date',
        'exit_date',
        'created_at',
        'updated_at'
    )
    list_filter = (
        'signal',
        'entry_date',
        'exit_date',
        'created_at'
    )
    search_fields = (
        'signal__instrument',
        'signal__magic_number'
    )
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    ordering = ('-created_at',)
