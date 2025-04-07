"""
Module for working with Interactive Brokers Gateway
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

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_project.settings")
django.setup()

# Configure logging
logger = logging.getLogger("bot")

# Disable ib_insync logs below WARNING level
util.logToConsole(level=logging.WARNING)


class TradingBot:
    """
    Class for working with Interactive Brokers Gateway
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
        Initialize connection to IB Gateway

        Args:
            host: IB Gateway host
            port: IB Gateway port
            client_id: Client ID
            max_retries: Maximum number of connection attempts
            retry_delay: Delay between attempts in seconds
        """
        logger.info("Initializing bot...")
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
        Connect to IB Gateway
        """
        if self.connected:
            return True

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Attempting to connect to IB Gateway ({attempt + 1}/{self.max_retries})"
                )
                self.ib.connect(self.host, self.port, clientId=self.client_id)
                self.connected = True
                logger.info("Successfully connected to IB Gateway")
                return True
            except Exception as e:
                logger.error(f"Error connecting to IB Gateway: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(
                        "Failed to connect to IB Gateway after all attempts"
                    )
                    return False

    def disconnect(self) -> None:
        """
        Disconnect from IB Gateway
        """
        if self.connected:
            try:
                self.ib.disconnect()
                self.connected = False
                logger.info("Disconnected from IB Gateway")
            except Exception as e:
                logger.error(f"Error disconnecting from IB Gateway: {str(e)}")

    def run(self) -> None:
        """
        Run the bot
        """
        try:
            if not self.connect():
                return

            logger.info("Initializing signal manager...")
            self.signal_manager = BotSignalManager(self.ib)
            logger.info("Signal manager successfully initialized")

            logger.info("Bot is running and waiting for signals...")

            self.signal_manager.manage_signals()
            self.disconnect()

        except Exception as e:
            logger.error(f"Critical error in bot: {str(e)}")
        finally:
            self.disconnect()


# Create global bot instance
bot = TradingBot()
