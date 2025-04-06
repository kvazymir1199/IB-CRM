"""
Задачи Celery для торгового бота
"""

import logging
from celery import shared_task
from django.apps import apps
from django.core.exceptions import AppRegistryNotReady

logger = logging.getLogger('trading_bot')

@shared_task(queue='signals_queue')
def check_signals():
    """
    Задача для проверки и создания сигналов
    """
    logger.info("Запуск задачи check_signals")
    try:
        # Проверяем готовность приложений Django
        apps.check_apps_ready()
        # Импортируем signal_manager только когда задача выполняется
        from trading_bot.signal_manager import signal_manager
    
        return signal_manager.check_signals()
    except AppRegistryNotReady:
        logger.warning("Приложения Django не готовы, повторная попытка через 5 секунд")
        # Если приложения не готовы, пробуем снова через 5 секунд
        check_signals.apply_async(countdown=5)
        return "Waiting for Django apps to be ready..."


@shared_task(queue='bot_queue', unique_on=['manage_bot'])
def manage_bot():
    """Задача для управления торговым ботом"""
    logger.info("Запуск задачи manage_bot")
    try:
        # Проверяем готовность приложений Django
        apps.check_apps_ready()
        
        # Проверяем состояние бота
        from trading_bot.models import BotState
        bot_state = BotState.get_state()
        
        if not bot_state.is_running:
            logger.info("Бот остановлен, пропускаем выполнение")
            return "Bot is stopped"
            
        from trading_bot.bot import bot
        logger.info("Бот запущен")
        return bot.run()
    except AppRegistryNotReady:
        logger.warning("Приложения Django не готовы, повторная попытка через 5 секунд")
        manage_bot.apply_async(countdown=5)
        return "Waiting for Django apps to be ready..."
    except Exception as e:
        logger.error(f"Ошибка в задаче manage_bot: {str(e)}", exc_info=True)
        raise e
