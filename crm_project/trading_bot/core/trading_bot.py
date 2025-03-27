"""
Модуль для работы с Interactive Brokers Gateway
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any

from ib_insync import IB, Contract, Order, Stock
from django.conf import settings
from django.utils import timezone

from trading_bot.models import BotSeasonalSignal
from signals.models import SeasonalSignal


class TradingBot:
    """
    Класс для работы с Interactive Brokers Gateway
    """
    def __init__(self):
        """
        Инициализация подключения к IB Gateway
        """
        self.ib = IB()
        self.connected = False
        self._connect()

    def _connect(self) -> None:
        """
        Установка соединения с IB Gateway
        """
        try:
            # Подключаемся к локальному IB Gateway
            self.ib.connect(
                host=os.getenv('IB_HOST', '127.0.0.1'),
                port=int(os.getenv('IB_PORT', '7496')),
                clientId=int(os.getenv('IB_CLIENT_ID', '0'))
            )
            self.connected = True
            print("Успешное подключение к IB Gateway")
        except Exception as e:
            print(f"Ошибка подключения к IB Gateway: {e}")
            self.connected = False

    def disconnect(self) -> None:
        """
        Отключение от IB Gateway
        """
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            print("Отключено от IB Gateway")

    def create_contract(self, symbol: str, exchange: str) -> Contract:
        """
        Создание контракта для торговли

        Args:
            symbol: Символ инструмента
            exchange: Биржа

        Returns:
            Contract: Объект контракта
        """
        return Stock(symbol, exchange, 'USD')

    def create_order(self, action: str, quantity: int) -> Order:
        """
        Создание ордера

        Args:
            action: Действие (BUY/SELL)
            quantity: Количество

        Returns:
            Order: Объект ордера
        """
        return Order(
            action=action,
            totalQuantity=quantity,
            orderType='MKT'
        )

    def place_order(self, contract: Contract, order: Order) -> bool:
        """
        Размещение ордера

        Args:
            contract: Контракт
            order: Ордер

        Returns:
            bool: Успешность размещения
        """
        try:
            trade = self.ib.placeOrder(contract, order)
            self.ib.sleep(1)  # Ждем подтверждения
            return trade.orderStatus.status == 'Filled'
        except Exception as e:
            print(f"Ошибка размещения ордера: {e}")
            return False

    def check_signals(self) -> Dict[str, Any]:
        """
        Проверка и выполнение сигналов

        Returns:
            Dict[str, Any]: Результаты выполнения
        """
        if not self.connected:
            return {'success': False, 'message': 'Нет подключения к IB Gateway'}

        results = {
            'success': True,
            'processed': 0,
            'executed': 0,
            'errors': []
        }

        try:
            # Получаем активные сигналы
            signals = BotSeasonalSignal.objects.filter(
                entry_date__lte=timezone.now(),
                exit_date__gt=timezone.now()
            )

            for signal in signals:
                results['processed'] += 1
                
                try:
                    # Создаем контракт
                    contract = self.create_contract(
                        symbol=signal.signal.symbol.symbol,
                        exchange=signal.signal.symbol.exchange
                    )

                    # Создаем и размещаем ордер
                    order = self.create_order('BUY', 1)  # Пример: 1 контракт
                    if self.place_order(contract, order):
                        results['executed'] += 1
                        print(f"Ордер выполнен для сигнала {signal.id}")
                    else:
                        results['errors'].append(f"Не удалось выполнить ордер для сигнала {signal.id}")

                except Exception as e:
                    results['errors'].append(f"Ошибка обработки сигнала {signal.id}: {e}")

        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Общая ошибка: {e}")

        return results

    def __del__(self):
        """
        Деструктор: отключаемся при удалении объекта
        """
        self.disconnect() 