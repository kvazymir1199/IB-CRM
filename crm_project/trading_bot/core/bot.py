"""
Модуль для работы с Interactive Brokers Gateway
"""
import os
import sys
import time
import django
from ib_insync import IB
from trading_bot.core.bot_signal_manager import BotSignalManager


# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()


class TradingBot:
    """
    Класс для работы с Interactive Brokers Gateway
    """
    def __init__(
        self,
        host: str = None,
        port: int = None,
        client_id: int = None,
        max_retries: int = 3,
        retry_delay: int = 5
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
        print("Инициализация бота...")
        sys.stdout.flush()
        
        self.ib = IB()
        self.connected = False
        self.host = host or os.getenv('IB_HOST', '127.0.0.1')
        self.port = port or int(os.getenv('IB_PORT', '4002'))
        self.client_id = client_id or int(os.getenv('IB_CLIENT_ID', '123'))
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        print("Инициализация менеджера сигналов...")
        sys.stdout.flush()
        try:
            self.signal_manager = BotSignalManager()
            print("Менеджер сигналов успешно инициализирован")
            sys.stdout.flush()
        except Exception as e:
            print(f"Ошибка при инициализации менеджера сигналов: {str(e)}")
            sys.stdout.flush()
            raise

        print(f"Параметры подключения:")
        print(f"- Хост: {self.host}")
        print(f"- Порт: {self.port}")
        print(f"- ID клиента: {self.client_id}")
        sys.stdout.flush()

        self._connect()

    def _connect(self) -> None:
        """
        Установка соединения с IB Gateway
        """
        retries = 0
        while retries < self.max_retries and not self.connected:
            try:
                print(
                    f"Попытка подключения к IB Gateway "
                    f"({retries + 1}/{self.max_retries})"
                )
                sys.stdout.flush()
                
                self.ib.connect(
                    host=self.host,
                    port=self.port,
                    clientId=self.client_id,
                    readonly=True  # Добавляем режим только для чтения
                )
                self.connected = True
                print("Успешное подключение к IB Gateway")
                sys.stdout.flush()
            except Exception as e:
                print(f"Ошибка подключения к IB Gateway: {str(e)}")
                sys.stdout.flush()
                retries += 1
                if retries < self.max_retries:
                    print(
                        f"Повторная попытка через {self.retry_delay} "
                        "секунд..."
                    )
                    sys.stdout.flush()
                    time.sleep(self.retry_delay)

    def disconnect(self) -> None:
        """
        Отключение от IB Gateway
        """
        if self.connected:
            try:
                self.ib.disconnect()
                self.connected = False
                print("Отключено от IB Gateway")
                sys.stdout.flush()
            except Exception as e:
                print(f"Ошибка при отключении от IB Gateway: {str(e)}")
                sys.stdout.flush()

    def is_connected(self) -> bool:
        """
        Проверка состояния подключения

        Returns:
            bool: True если подключено, False если нет
        """
        return self.connected

    def run(self) -> None:
        """
        Запуск бота в режиме ожидания
        """
        try:
            print("Бот запущен и ожидает сигналов...")
            sys.stdout.flush()
            
            # Выводим информацию об активных сигналах
            self.signal_manager.print_active_signals()
            
            while True:
                if not self.is_connected():
                    print("Потеряно соединение, переподключение...")
                    sys.stdout.flush()
                    self._connect()
                # Проверяем сигналы каждые 5 секунд
                self.signal_manager.print_active_signals()
                time.sleep(5)  # Проверяем каждые 5 секунд
        except KeyboardInterrupt:
            print("\nПолучен сигнал завершения работы")
            sys.stdout.flush()
        finally:
            self.disconnect()

    def __del__(self):
        """
        Деструктор: отключаемся при удалении объекта
        """
        self.disconnect()


if __name__ == "__main__":
    print("Запуск торгового бота...")
    sys.stdout.flush()
    
    # Создаем и запускаем бота
    bot = TradingBot()
    if bot.is_connected():
        print("Бот успешно подключен и готов к работе")
        sys.stdout.flush()
        bot.run()  # Запускаем бота в режиме ожидания
    else:
        print("Не удалось подключить бота")
        sys.stdout.flush()
