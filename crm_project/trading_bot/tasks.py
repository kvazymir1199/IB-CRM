"""
Задачи Celery для торгового бота
"""

from celery import shared_task
from django.apps import apps


@shared_task
def check_signals():
    """
    Задача для проверки и создания сигналов
    """
    # Импортируем signal_manager только когда задача выполняется
    from .core.signal_manager import signal_manager

    return signal_manager.check_signals()
