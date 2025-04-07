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
    Task for checking and creating signals
    """
    logger.info("Starting check_signals task")
    try:
        # Check if Django apps are ready
        apps.check_apps_ready()
        # Импортируем signal_manager только когда задача выполняется
        from trading_bot.signal_manager import signal_manager
    
        return signal_manager.check_signals()
    except AppRegistryNotReady:
        logger.warning("Django apps are not ready, retrying in 5 seconds")
        # Если приложения не готовы, пробуем снова через 5 секунд
        check_signals.apply_async(countdown=5)
        return "Waiting for Django apps to be ready..."


@shared_task(queue='bot_queue', unique_on=['manage_bot'])
def manage_bot():
    """Task for managing the trading bot"""
    logger.info("Starting manage_bot task")
    try:
        # Check if Django apps are ready
        apps.check_apps_ready()
        
        # Проверяем состояние бота
        from trading_bot.models import BotState
        bot_state = BotState.get_state()
        
        if not bot_state.is_running:
            logger.info("Bot is stopped, skipping execution")
            return "Bot is stopped"
            
        from trading_bot.bot import bot
        logger.info("Bot is running")
        return bot.run()
    except AppRegistryNotReady:
        logger.warning("Django apps are not ready, retrying in 5 seconds")
        manage_bot.apply_async(countdown=5)
        return "Waiting for Django apps to be ready..."
    except Exception as e:
        logger.error(f"Error in manage_bot task: {str(e)}", exc_info=True)
        raise e
