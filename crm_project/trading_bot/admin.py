"""
Административный интерфейс для торгового бота
"""

from django.contrib import admin
from .models import BotSeasonalSignal, BotState


@admin.register(BotSeasonalSignal)
class BotSeasonalSignalAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для BotSeasonalSignal
    """

    list_display = (
        "pk",
        "signal",
        "entry_date",
        "exit_date",
        "created_at",
        "updated_at",
        "status",
        "order_id",
    )
    list_filter = ("status", "signal__symbol", "entry_date", "exit_date", "created_at")
    search_fields = ("signal__symbol", "order_id")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(BotState)
class BotStateAdmin(admin.ModelAdmin):
    list_display = ("is_running", "last_updated")
    readonly_fields = ("last_updated",)
    actions = None  # Отключаем стандартные действия

    def has_add_permission(self, request):
        """Запрещаем создание новых записей"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление записей"""
        return False
