"""
Модуль для управления позициями торгового бота
"""

import logging
import os
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from decimal import Decimal

from datetime import datetime, timedelta
import dataclasses
import pytz

from django.utils import timezone
from ib_insync import MarketOrder, LimitOrder, StopOrder, ContFuture, IB
from trading_bot.models import BotSeasonalSignal

if TYPE_CHECKING:
    from .bot import TradingBot

# Создаем директорию для логов, если она не существует
log_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
log_file = os.path.join(log_dir, 'trading_bot.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Создаем логгер для модуля
logger = logging.getLogger('trading_bot.core.bot_signal_manager')

# Проверяем права доступа к файлу логов
try:
    with open(log_file, 'a') as f:
        pass
    os.remove(log_file)
except (IOError, OSError) as e:
    logger.error(f"Ошибка доступа к файлу логов: {e}")


@dataclasses.dataclass
class TradingHours:
    status: str
    start: datetime
    end: datetime


def parse_data(contract_details) -> list:
    trading_hours = []
    data = contract_details.tradingHours
    tz = contract_details.timeZoneId
    for entry in data.split(";"):
        data, status = entry.split(":", 1)
        if status == "CLOSED":
            trading_hours.append(
                TradingHours(status="CLOSED", start=None, end=None)
            )
        else:
            start = datetime(
                year=int(entry[0:4]),
                month=int(entry[4:6]),
                day=int(entry[6:8]),
                hour=int(entry[9:11]),
                minute=int(entry[11:13]),
                tzinfo=pytz.timezone(tz),
            )
            end = datetime(
                year=int(entry[14:18]),
                month=int(entry[18:20]),
                day=int(entry[20:22]),
                hour=int(entry[23:25]),
                minute=int(entry[25:27]),
                tzinfo=pytz.timezone(tz),
            )
            trading_hours.append(
                TradingHours(
                    status="OPEN",
                    start=start,
                    end=end,
                )
            )
    return trading_hours


class BotSignalManager:
    """
    Класс для управления сигналами торгового бота
    """
    def __init__(self, ib_connector: IB):
        self.ib_connector = ib_connector
        self.logger = logging.getLogger('trading_bot.core.bot_signal_manager')

    # def process_signal(self, signal: Dict[str, Any]) -> None:
    #     """
    #     Обработка торгового сигнала
    #
    #     Args:
    #         signal: Словарь с параметрами сигнала
    #     """
    #     try:
    #         self.logger.info(f"Начало обработки сигнала: {signal}")
    #         self._validate_signal(signal)
    #         self._open_order(signal)
    #         self.logger.info("Сигнал успешно обработан")
    #     except Exception as e:
    #         self.logger.error(f"Ошибка при обработке сигнала: {e}")
    #         raise

    def manage_signals(self) -> None:
        """
        Управление сигналами торгового бота
        """
        self.logger.info("Начало работы метода manage_signals")
        try:
            self.logger.info("Получение всех сигналов из базы данных")
            signals = BotSeasonalSignal.objects.all(
                # exit_date__gt=timezone.now()
            ).select_related("signal", "signal__symbol")
            
            self.logger.info(f"Найдено сигналов: {signals.count()}")
            
            for signal in signals:
                self.logger.info(f"Обработка сигнала ID: {signal.id}")
                self.logger.info(f"Статус сигнала: {signal.status}")
                self.logger.info(f"Дата входа: {signal.entry_date}")
                self.logger.info(f"Дата выхода: {signal.exit_date}")
                
                if signal.status == "awaiting":
                    self.logger.info(f"Сигнал {signal.id} в статусе awaiting")
                    if signal.entry_date <= timezone.now():
                        self.logger.info(f"Сигнал {signal.id} готов к открытию позиции")
                        # TODO: Добавить логику открытия позиции
                        signal.status = "open"
                        signal.save()
                        self.logger.info(f"Статус сигнала {signal.id} изменен на open")
                elif signal.status == "open":
                    self.logger.info(f"Сигнал {signal.id} в статусе open")
                    if signal.exit_date <= timezone.now():
                        self.logger.info(f"Сигнал {signal.id} готов к закрытию позиции")
                        # TODO: Добавить логику закрытия позиции
                        signal.status = "close"
                        signal.save()
                        self.logger.info(f"Статус сигнала {signal.id} изменен на close")
                
            self.logger.info("Завершение работы метода manage_signals")
            
        except Exception as e:
            self.logger.error(f"Ошибка в методе manage_signals: {str(e)}")
            raise

    def _handle_signal(self, _signal: BotSeasonalSignal):
        """
        Обработка отдельного сигнала

        Args:
            _signal: Объект BotSeasonalSignal
        """
        try:
            self.logger.info(f"Обработка сигнала {_signal.pk}")
            entry_time = timezone.localtime(_signal.entry_date)
            exit_time = timezone.localtime(_signal.exit_date)

            if not _signal.order_id:
                self.logger.info(f"Сигнал {_signal.pk} не имеет открытого ордера")

                if self.current_time < entry_time:
                    self.logger.info(f"Время входа не наступило для сигнала {_signal.pk}")
                    return

                self.logger.info(f"Время входа наступило для сигнала {_signal.pk}")
                self.logger.info("Получение контракта...")
                contract = self._get_contract(_signal)

                if not contract:
                    self.logger.warning(f"Не удалось получить контракт для сигнала {_signal.pk}")
                    return

                self.logger.info("Открытие ордера...")
                if not self._is_trading_time(contract):
                    self.logger.info(f"Рынок закрыт: {self.current_time}")
                    self.logger.info(f"Время входа не наступило для сигнала {_signal.pk}")
                    return
                try:
                    self._open_order(_signal, contract.contract)
                except Exception as e:
                    self.logger.error(f"Ошибка при открытии ордера: {str(e)}", exc_info=True)
                    return

            if self.current_time >= exit_time:
                self.logger.info(f"Время выхода наступило для сигнала {_signal.pk}")
                # TODO: Добавить логику закрытия позиции

        except Exception as e:
            self.logger.error(f"Ошибка при обработке сигнала: {str(e)}", exc_info=True)

    def _get_contract(self, _signal: BotSeasonalSignal) -> ContFuture | None:
        """
        Создает объект контракта для запроса

        Args:
            _signal: Объект BotSeasonalSignal

        Returns:
            ContFuture: Объект контракта
        """
        self.logger.info(f"Создание контракта для сигнала {_signal.pk}")
        self.logger.info(f"Символ: {_signal.signal.symbol.financial_instrument}")
        self.logger.info(f"Биржа: {_signal.signal.symbol.exchange}")

        contract = ContFuture(
            symbol=_signal.signal.symbol.financial_instrument,
            exchange=_signal.signal.symbol.exchange,
            currency="USD",
        )

        # Получаем детали контракта
        try:
            details = self.ib_connector.reqContractDetails(contract)
            if details:
                return details[0]
            else:
                self.logger.warning("Не найдены детали контракта")
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении деталей контракта: {str(e)}")
            return None

    def _is_trading_time(self, contract_details) -> bool:
        """
        Проверяет, является ли текущее время торговым

        Args:
            contract_details: Детали контракта

        Returns:
            bool: True если сейчас торговое время, False если нет
        """
        try:
            # current_time = timezone.localtime()
            # Получаем торговые часы для текущей даты
            trading_schedule = contract_details.tradingHours
            if not trading_schedule:
                self.logger.warning("Нет информации о торговых часах")
                return False
            trading_schedule = parse_data(contract_details)

            for day in trading_schedule:

                if day.status == "OPEN":
                    if self.current_time >= day.start and self.current_time <= day.end:
                        self.logger.info(f"торговые часы открыты: {day.start} - {day.end} сейчас {self.current_time}")
                        return True
            return False

        except Exception as e:
            self.logger.error(f"Ошибка при проверке торговых часов: {str(e)}")
            raise (e)
            return False

    def _open_order(self, signal: BotSeasonalSignal, contract: ContFuture) -> None:
        """Открывает ордер для сигнала"""
        try:
            self.logger.info(f"[1] Начало открытия ордера для сигнала {signal.pk}, контракт {contract.symbol}")
            self.logger.info("[2] Запрос исторических данных...")

            bars = self.ib_connector.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr='1 D',
                barSizeSetting='1 min',
                whatToShow='TRADES',
                useRTH=True,
                timeout=10
            )
            self.logger.info(f"[3] Получены исторические данные: {len(bars)} баров")

            actual_price = float(bars[-1].close)
            self.logger.info(f"[4] Рассчитана актуальная цена для {contract.symbol}: {actual_price}")

            parent_id = self.ib_connector.client.getReqId()
            self.logger.info(f"[5] Получен ID для родительского ордера: {parent_id}")

            entry_action = self.get_entry_direction(signal)
            exit_action = self.get_exit_direction(signal)
            self.logger.info(f"[6] Определены направления: вход={entry_action}, выход={exit_action}")

            # Создаем лимитный ордер
            self.logger.info("[7] Создание лимитного ордера...")
            limit_order = LimitOrder(
                action=entry_action,
                totalQuantity=1,  # Временное значение
                lmtPrice=actual_price,
                orderId=parent_id,
            )

            # Устанавливаем время активации
            activation_time = (datetime.now() + timedelta(minutes=5)).strftime('%Y%m%d %H:%M:%S')
            limit_order.goodAfterTime = activation_time
            self.logger.info(f"[8] Установлено время активации ордера: {activation_time}")

            # Расчет стоп-лосса
            self.logger.info("[9] Расчет стоп-лосса...")
            stoploss = self.calculate_stoploss(signal, actual_price)
            self.logger.info(f"[10] Рассчитана стоп-цена: {stoploss}")

            # Расчет размера позиции
            self.logger.info("[11] Расчет размера позиции...")
            balance = float(self.get_balance())
            self.logger.info(f"[12] Получен баланс счета: {balance}")

            lots = self.calculate_position_size(
                balance=balance,
                entry_price=actual_price,
                stop_loss=stoploss,
                multiplier=float(contract.multiplier),
                risk_percent=signal.signal.risk
            )
            self.logger.info(f"[13] Рассчитан размер позиции: {lots} контрактов")

            # Обновляем количество в ордере
            limit_order.totalQuantity = lots
            self.logger.info("[14] Обновлено количество в лимитном ордере")

            # Размещаем лимитный ордер
            self.logger.info("[15] Размещение лимитного ордера...")
            trade = self.ib_connector.placeOrder(contract, limit_order)
            self.logger.info(f"[16] Лимитный ордер размещен, ID: {trade.order.orderId}")

            # Создаем и размещаем стоп-ордер
            self.logger.info("[17] Создание стоп-ордера...")
            stop_order = StopOrder(
                action=exit_action,
                totalQuantity=lots,
                stopPrice=stoploss
            )
            stop_order.parentId = trade.order.orderId
            self.logger.info(f"[18] Связываем стоп-ордер с родительским ордером {trade.order.orderId}")

            self.logger.info("[19] Размещение стоп-ордера...")
            stop_trade = self.ib_connector.placeOrder(contract, stop_order)
            self.logger.info(f"[20] Стоп-ордер размещен, ID: {stop_trade.order.orderId}")
            self.ib_connector.sleep(1)

            # Проверим статус
            status = stop_trade.orderStatus.status
            self.logger.info(f"[DEBUG] Статус стоп-ордера: {status}")

            # Проверим логи ордера
            if stop_trade.log:
                for log in stop_trade.log:
                    self.logger.info(f"[DEBUG] Стоп-ордер лог: {log.message}")
            # Сохраняем ID ордера в сигнале
            signal.order_id = parent_id
            signal.save()
            self.logger.info(f"[21] Сохранен ID ордера {parent_id} в сигнале {signal.pk}")

            self.logger.info(f"""[22] ИТОГ размещения ордеров:
            Символ: {contract.symbol}
            Направление: {entry_action}
            Цена входа: {actual_price}
            Стоп-лосс: {stoploss}
            Количество: {lots}
            ID лимитного ордера: {trade.order.orderId}
            ID стоп-ордера: {stop_trade.order.orderId}
            Время активации: {activation_time}
            """)

        except Exception as e:
            self.logger.error(f"[ERROR] Ошибка при открытии ордера: {str(e)}", exc_info=True)
            raise

    def get_balance(self) -> float:
        account_summary = self.ib_connector.accountSummary()
        net_liquidation_values = [val for val in account_summary if val.tag == 'NetLiquidation']
        for value in net_liquidation_values:
            print(f"Account: {value.account}, NetLiquidation: {value.value} {value.currency}")
            return value.value

    def get_entry_direction(self, signal: BotSeasonalSignal) -> str:
        return "BUY" if signal.signal.direction == "LONG" else "SELL"

    def get_exit_direction(self, signal: BotSeasonalSignal) -> str:
        return "SELL" if signal.signal.direction == "LONG" else "BUY"

    def calculate_stoploss(self, signal: BotSeasonalSignal, actual_price):
        is_long = signal.signal.direction == "LONG"
        stoploss_value = float(signal.signal.stoploss)
        if signal.signal.stoploss_type == "POINTS":
            stop_price = round(
                actual_price - stoploss_value if is_long
                else actual_price + stoploss_value, 2
            )
        else:
            stop_price = round(
                actual_price * (1 - stoploss_value / 100) if is_long
                else actual_price * (1 + stoploss_value / 100), 2
            )
        return stop_price

    def calculate_position_size(self, balance, entry_price, stop_loss, multiplier: int | float = 1, risk_percent=2):
        """
        Рассчитывает размер позиции на основе риска
        
        Args:
            balance (float): Баланс счета
            entry_price (float): Цена входа
            stop_loss (float): Цена стоп-лосса
            multiplier (float): Множитель контракта
            risk_percent (float): Процент риска от баланса
            
        Returns:
            int: Количество контрактов
        """
        try:
            # Преобразуем все значения к float
            balance = float(balance)
            entry_price = float(entry_price)
            stop_loss = float(stop_loss)
            multiplier = float(multiplier)
            risk_percent = float(risk_percent)
            
            self.logger.info(f"Расчет размера позиции:")
            self.logger.info(f"Баланс: {balance}")
            self.logger.info(f"Цена входа: {entry_price}")
            self.logger.info(f"Стоп-лосс: {stop_loss}")
            self.logger.info(f"Множитель: {multiplier}")
            self.logger.info(f"Процент риска: {risk_percent}%")
            
            risk_amount = balance * (risk_percent / 100)  # Сколько денег рискуем
            risk_per_unit = abs(entry_price - stop_loss) * multiplier  # Убыток на 1 контракт
            
            self.logger.info(f"Сумма риска: {risk_amount}")
            self.logger.info(f"Риск на 1 контракт: {risk_per_unit}")
            
            if risk_per_unit == 0:
                self.logger.warning("Риск на контракт равен 0, возвращаем 1 контракт")
                return 1
                
            quantity = risk_amount / risk_per_unit  # Количество контрактов
            result = max(1, int(quantity))  # Минимум 1 контракт
            
            self.logger.info(f"Рассчитанное количество контрактов: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка при расчете размера позиции: {str(e)}")
            self.logger.info("Возвращаем минимальный размер позиции: 1")
            return 1
