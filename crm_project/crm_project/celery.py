"""
Конфигурация Celery для проекта
"""
import os
from celery import Celery
from django.conf import settings

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')

# Создаем экземпляр Celery
app = Celery('crm_project')

# Загружаем настройки из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Импортируем задачи
from trading_bot import tasks

# Автоматически находим и регистрируем задачи из всех приложений
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Настраиваем периодические задачи
app.conf.beat_schedule = {
    'check-signals': {
        'task': 'trading_bot.tasks.check_signals',
        'schedule': 60.0,  # каждую минуту
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Тестовая задача"""
    print(f'Request: {self.request!r}') 