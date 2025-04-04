"""
Модуль для управления позициями торгового бота
"""

import logging
from typing import TYPE_CHECKING

from datetime import datetime, timedelta
import dataclasses
import pytz
import time

from django.utils import timezone
from ib_insync import LimitOrder, StopOrder, ContFuture, IB, util
from ib_insync.objects import ExecutionFilter
from ib_insync.order import MarketOrder

from trading_bot.models import BotSeasonalSignal

if TYPE_CHECKING:
    pass

# Создаем логгер для модуля
logger = logging.getLogger('trading_bot.core.bot_signal_manager')

# Отключаем логи ib_insync ниже уровня WARNING
util.logToConsole(level=logging.WARNING)

# Константы для таймаутов
HISTORICAL_DATA_TIMEOUT = 30  # Увеличенный таймаут для исторических данных
ORDER_TIMEOUT = 20  # Таймаут для операций с ордерами
CONTRACT_DETAILS_TIMEOUT = 15  # Таймаут для получения деталей контракта
MAX_RETRIES = 3  # Максимальное количество попыток
RETRY_DELAY = 5  # Задержка между попытками в секундах


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
        self.logger = logger  # Используем тот же логгер

    def get_current_time(self) -> datetime:
        """
        Получение текущего времени от IB Gateway
        """

        return self.ib_connector.reqCurrentTime()

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
            self.current_time = self.get_current_time()
            if self.current_time is None:
                self.logger.error("Не удалось получить текущее время")
                return
            for signal in signals:
                self._handle_signal(signal)

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
            self.logger.info("=" * 20 + f" Обработка сигнала {_signal.id} " + "=" * 20)
            entry_time = timezone.localtime(_signal.entry_date)
            exit_time = timezone.localtime(_signal.exit_date)
            contract = self._get_contract(_signal)
            if not _signal.order_id:
                self.logger.info(f"Сигнал {_signal.pk} не имеет открытого ордера")

                if self.current_time < entry_time:
                    self.logger.info(f"Время входа не наступило для сигнала {_signal.pk}")
                    return

                self.logger.info(f"Время входа наступило для сигнала {_signal.pk}")
                self.logger.info("Получение контракта...")


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
                self.check_and_close_position(_signal.order_id, contract)
            self.logger.info("=" * 20 + f" Завершение обработки сигнала {_signal.id} " + "=" * 20)
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

        # Получаем детали контракта с повторными попытками
        for attempt in range(MAX_RETRIES):
            try:
                self.logger.info(f"Попытка получения деталей контракта ({attempt + 1}/{MAX_RETRIES})")
                details = self.ib_connector.reqContractDetails(contract)
                if details:
                    return details[0]
                else:
                    self.logger.warning("Не найдены детали контракта")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                    continue
            except Exception as e:
                self.logger.error(f"Ошибка при получении деталей контракта: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                continue
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

            # Получаем исторические данные с повторными попытками
            bars = None
            for attempt in range(MAX_RETRIES):
                try:
                    self.logger.info(f"Попытка получения исторических данных ({attempt + 1}/{MAX_RETRIES})")
                    bars = self.ib_connector.reqHistoricalData(
                        contract,
                        endDateTime='',
                        durationStr='1 D',
                        barSizeSetting='1 min',
                        whatToShow='TRADES',
                        useRTH=True,
                        timeout=HISTORICAL_DATA_TIMEOUT
                    )
                    if bars:
                        break
                except Exception as e:
                    self.logger.error(f"Ошибка при получении исторических данных: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                    continue

            if not bars:
                raise Exception("Не удалось получить исторические данные после всех попыток")

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

            # Размещаем лимитный ордер с повторными попытками
            trade = None
            for attempt in range(MAX_RETRIES):
                try:
                    self.logger.info(f"[15] Попытка размещения лимитного ордера ({attempt + 1}/{MAX_RETRIES})...")
                    trade = self.ib_connector.placeOrder(contract, limit_order)
                    if trade:
                        break
                except Exception as e:
                    self.logger.error(f"Ошибка при размещении лимитного ордера: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                    continue

            if not trade:
                raise Exception("Не удалось разместить лимитный ордер после всех попыток")

            self.logger.info(f"[16] Лимитный ордер размещен, ID: {trade.order.orderId}")

            # Создаем и размещаем стоп-ордер с повторными попытками
            self.logger.info("[17] Создание стоп-ордера...")
            stop_order = StopOrder(
                action=exit_action,
                totalQuantity=lots,
                stopPrice=stoploss
            )
            stop_order.parentId = trade.order.orderId
            self.logger.info(f"[18] Связываем стоп-ордер с родительским ордером {trade.order.orderId}")

            stop_trade = None
            for attempt in range(MAX_RETRIES):
                try:
                    self.logger.info(f"[19] Попытка размещения стоп-ордера ({attempt + 1}/{MAX_RETRIES})...")
                    stop_trade = self.ib_connector.placeOrder(contract, stop_order)
                    if stop_trade:
                        break
                except Exception as e:
                    self.logger.error(f"Ошибка при размещении стоп-ордера: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                    continue

            if not stop_trade:
                raise Exception("Не удалось разместить стоп-ордер после всех попыток")

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

    def check_and_close_position(self, order_id: int, contract: ContFuture) -> bool:
        """
        Проверяет и закрывает позицию если необходимо
        
        Args:
            order_id: ID ордера (используется только для логов)
            contract: Объект контракта
            
        Returns:
            bool: True если позиция успешно закрыта, False в противном случае
        """
        try:
            self.logger.info("=" * 40)
            self.logger.info(
                f"=== Начало проверки позиции по {contract.contract.symbol} ==="
            )
            
            # 1. Проверка наличия позиции
            self.logger.info("Проверка наличия открытой позиции...")
            positions = self.ib_connector.positions()
            
            # Логируем все позиции для отладки
            self.logger.info(f"Получено {len(positions)} позиций:")
            for i, pos in enumerate(positions):
                self.logger.info(
                    f"  #{i+1}: symbol={pos.contract.symbol}, "
                    f"position={pos.position}, "
                    f"avgCost={pos.avgCost}"
                )
            
            position = next(
                (p for p in positions if p.contract.symbol == contract.contract.symbol),
                None
            )
            
            if not position:
                self.logger.warning(
                    f"Позиция по {contract.contract.symbol} не найдена в списке позиций."
                )
                return False
                
            if position.position == 0:
                self.logger.info(f"Позиция по {contract.contract.symbol} имеет нулевой объем.")
                return False
                
            self.logger.info(
                f"Найдена позиция по {contract.contract.symbol}: "
                f"объем={position.position}, средняя цена={position.avgCost}"
            )
            
            # 2. Проверка наличия активных стоп-ордеров
            self.logger.info("Проверка наличия активных стоп-ордеров...")
            open_orders = self.ib_connector.openOrders()
            
            # Логируем все открытые ордера
            self.logger.info(f"Получено {len(open_orders)} открытых ордеров:")
            for i, order in enumerate(open_orders[:5]):  # Выводим первые 5 для краткости
                self.logger.info(
                    f"  #{i+1}: orderId={order.orderId}, "
                    f"action={order.action}, "
                    f"orderType={order.orderType}, "
                    f"totalQuantity={order.totalQuantity}"
                )
            
            # Ищем стоп-ордера для этого символа контракта
            stop_orders = [
                o for o in open_orders 
                if o.orderType == 'STP' and o.contract.symbol == contract.contract.symbol
            ]
            
            # Если найдены активные стоп-ордера для этого символа, не закрываем позицию
            if stop_orders:
                self.logger.info(
                    f"Найдены активные стоп-ордера для {contract.contract.symbol}: {len(stop_orders)}. "
                    f"Стоп-ордера закроют позицию автоматически."
                )
                return False
            else:
                self.logger.info(f"Активные стоп-ордера для {contract.contract.symbol} не найдены")
            
            # 3. Закрытие позиции
            self.logger.info(
                f"Подготовка к закрытию позиции по {contract.contract.symbol}"
            )
            action = 'SELL' if position.position > 0 else 'BUY'
            quantity = abs(position.position)
            
            self.logger.info(
                f"Создание ордера: {action} {quantity} {contract.contract.symbol}"
            )
            
            close_order = MarketOrder(action, quantity)
            close_order.orderId = self.ib_connector.client.getReqId()  # Генерируем новый ID
            self.logger.info(f"Назначен новый ID ордера: {close_order.orderId}")
            
            trade = self.ib_connector.placeOrder(contract.contract, close_order)
            
            if not trade:
                self.logger.error(
                    f"Не удалось разместить ордер на закрытие {contract.contract.symbol}."
                )
                return False
                
            self.logger.info(
                f"Ордер на закрытие размещен: orderId={trade.order.orderId}, "
                f"status={trade.orderStatus.status}, "
                f"{action} {quantity} {contract.contract.symbol}"
            )
            
            # 4. Проверка статуса закрытия
            wait_time = 5  # Увеличиваем время ожидания для заполнения ордера
            self.logger.info(f"Ожидание исполнения ордера закрытия ({wait_time} сек)...")
            self.ib_connector.sleep(wait_time)
            
            # Проверяем, была ли закрыта позиция
            positions = self.ib_connector.positions()
            position = next(
                (p for p in positions if p.contract.symbol == contract.contract.symbol),
                None
            )
            
            if not position or position.position == 0:
                self.logger.info(
                    f"Позиция по {contract.contract.symbol} успешно закрыта"
                )
                return True
            else:
                self.logger.warning(
                    f"Не удалось полностью закрыть позицию по {contract.contract.symbol}, "
                    f"оставшийся объем: {position.position}"
                )
                return False
                
        except Exception as e:
            self.logger.error(
                f"Ошибка при закрытии позиции {contract.contract.symbol}: {str(e)}",
                exc_info=True
            )
            # Логируем дополнительную информацию об ошибке
            import traceback
            self.logger.error(f"Детали ошибки: {traceback.format_exc()}")
            return False
        finally:
            self.logger.info(
                f"=== Завершение проверки позиции по {contract.contract.symbol} ==="
            )
            self.logger.info("=" * 40)
