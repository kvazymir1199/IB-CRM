"""
Модуль для работы с Interactive Brokers Gateway
"""

import logging
import os
import sys
import time
import random
import django
from ib_insync import IB, util
from trading_bot.bot_signal_manager import BotSignalManager
from django.conf import settings

# Настраиваем Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

# Настраиваем логирование
logger = logging.getLogger("bot")

# Отключаем логи ib_insync ниже уровня WARNING
util.logToConsole(level=logging.WARNING)


class TradingBot:
    """
    Класс для работы с Interactive Brokers Gateway
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        client_id: int = None,
        max_retries: int = 1,
        retry_delay: int = 2,
    ):
        """
        Инициализация подключения к IB Gateway

        Args:
            host: Хост IB Gateway
            port: Порт IB Gateway
            client_id: ID клиента
            max_retries: Максимальное количество попыток подключения
            retry_delay: Задержка между попытками в секундах
        """
        logger.info("Инициализация бота...")
        sys.stdout.flush()

        self.ib = IB()
        self.connected = False
        self.host = host or settings.IB_HOST
        self.port = port or settings.IB_PORT
        self.client_id = random.randint(100, 9999)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.signal_manager = None

    def connect(self) -> bool:
        """
        Подключение к IB Gateway
        """
        if self.connected:
            return True

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Попытка подключения к IB Gateway ({attempt + 1}/{self.max_retries})"
                )
                self.ib.connect(self.host, self.port, clientId=self.client_id)
                self.connected = True
                logger.info("Успешное подключение к IB Gateway")
                return True
            except Exception as e:
                logger.error(f"Ошибка подключения к IB Gateway: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(
                        "Не удалось подключиться к IB Gateway после всех попыток"
                    )
                    return False

    def disconnect(self) -> None:
        """
        Отключение от IB Gateway
        """
        if self.connected:
            try:
                self.ib.disconnect()
                self.connected = False
                logger.info("Отключено от IB Gateway")
            except Exception as e:
                logger.error(f"Ошибка при отключении от IB Gateway: {str(e)}")

    def run(self) -> None:
        """
        Запуск бота
        """
        try:
            if not self.connect():
                return

            logger.info("Инициализация менеджера сигналов...")
            self.signal_manager = BotSignalManager(self.ib)
            logger.info("Менеджер сигналов успешно инициализирован")

            logger.info("Бот запущен и ожидает сигналов...")

            self.signal_manager.manage_signals()
            self.disconnect()

        except Exception as e:
            logger.error(f"Критическая ошибка в боте: {str(e)}")
        finally:
            self.disconnect()


# Создаем глобальный экземпляр бота
bot = TradingBot()
