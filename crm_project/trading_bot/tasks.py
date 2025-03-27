"""
Задачи Celery для торгового бота
"""

from celery import shared_task
from django.apps import apps
from django.core.exceptions import AppRegistryNotReady


@shared_task
def check_signals():
    """
    Задача для проверки и создания сигналов
    """
    try:
        # Проверяем готовность приложений Django
        apps.check_apps_ready()
        # Импортируем signal_manager только когда задача выполняется
        from .core.signal_manager import signal_manager
        return signal_manager.check_signals()
    except AppRegistryNotReady:
        # Если приложения не готовы, пробуем снова через 5 секунд
        check_signals.apply_async(countdown=5)
        return "Waiting for Django apps to be ready..."
