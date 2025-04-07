"""
Module for managing trading bot positions
"""

import logging
from typing import TYPE_CHECKING

from datetime import datetime, timedelta
import dataclasses
from zoneinfo import ZoneInfo
import pytz
import time

from django.utils import timezone
from ib_insync import LimitOrder, StopOrder, ContFuture, IB, util, MarketOrder

from crm_project.settings import TIME_ZONE
from trading_bot.models import BotSeasonalSignal, TradeStatus

if TYPE_CHECKING:
    pass

# Create logger for module
logger = logging.getLogger("trading_bot.core.bot_signal_manager")

# Disable ib_insync logs below WARNING level
util.logToConsole(level=logging.WARNING)

# Timeout constants
HISTORICAL_DATA_TIMEOUT = 30  # Increased timeout for historical data
ORDER_TIMEOUT = 20  # Timeout for order operations
CONTRACT_DETAILS_TIMEOUT = 15  # Timeout for contract details
MAX_RETRIES = 3  # Maximum retry attempts
RETRY_DELAY = 5  # Delay between retries in seconds


@dataclasses.dataclass
class TradingHours:
    status: str
    start: datetime
    end: datetime


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
        current_time = self.ib_connector.reqCurrentTime()

        return current_time.astimezone(ZoneInfo(TIME_ZONE))

    def manage_signals(self) -> None:
        """
        Managing trading bot signals
        """
        self.logger.info("Starting manage_signals method")
        try:
            self.logger.info("Getting all signals from database")
            signals = BotSeasonalSignal.objects.all(
                # exit_date__gt=timezone.now()
            ).select_related("signal", "signal__symbol")

            self.logger.info(f"Found signals: {signals.count()}")
            self.current_time = self.get_current_time()

            if self.current_time is None:
                self.logger.error("Failed to get current time")
                return
            for signal in signals:
                self._handle_signal(signal)

            self.logger.info("Finishing manage_signals method")

        except Exception as e:
            self.logger.error(f"Error in manage_signals method: {str(e)}")
            raise

    def _handle_signal(self, _signal: BotSeasonalSignal):
        """
        Обработка отдельного сигнала

        Args:
            _signal: Объект BotSeasonalSignal
        """
        try:
            self.logger.info("=" * 20 + f" Processing signal {_signal.id} " + "=" * 20)
            entry_time = timezone.localtime(_signal.entry_date)
            exit_time = timezone.localtime(_signal.exit_date)
            contract = self._get_contract(_signal)

            if not _signal.order_id:
                self.logger.info(f"Signal {_signal.pk} has no open order")

                if self.current_time < entry_time:
                    self.logger.info(f"Entry time not reached for signal {_signal.pk}")
                    self.logger.info(
                        f"Current time: {self.current_time} entry time: {entry_time}"
                    )
                    return

                self.logger.info(f"Entry time reached for signal {_signal.pk}")
                self.logger.info("Getting contract...")

                if not contract:
                    self.logger.warning(
                        f"Failed to get contract for signal {_signal.pk}"
                    )
                    return

                self.logger.info("Opening order...")
                if not self._is_trading_time(contract):
                    self.logger.info(f"Market is closed: {self.current_time}")
                    self.logger.info(f"Entry time not reached for signal {_signal.pk}")
                    return
                try:
                    self._open_order(_signal, contract.contract)
                except Exception as e:
                    self.logger.error(f"Error opening order: {str(e)}", exc_info=True)
                    return

            if self.current_time >= exit_time:
                if _signal.status != TradeStatus.CLOSE:
                    self.logger.info(f"Exit time reached for signal {_signal.pk}")
                    self.check_and_close_position(_signal.order_id, contract)
                    _signal.status = TradeStatus.CLOSE
                    _signal.save()
                    self.logger.info(f"Signal {_signal.pk} closed")
            self.logger.info(
                "=" * 20 + f" Finished processing signal {_signal.id} " + "=" * 20
            )
        except Exception as e:
            self.logger.error(f"Error processing signal: {str(e)}", exc_info=True)

    def _get_contract(self, _signal: BotSeasonalSignal) -> ContFuture | None:
        """
        Создает объект контракта для запроса

        Args:
            _signal: Объект BotSeasonalSignal

        Returns:
            ContFuture: Объект контракта
        """
        self.logger.info(f"Creating contract for signal {_signal.pk}")
        self.logger.info(f"Symbol: {_signal.signal.symbol.financial_instrument}")
        self.logger.info(f"Exchange: {_signal.signal.symbol.exchange}")

        contract = ContFuture(
            symbol=_signal.signal.symbol.financial_instrument,
            exchange=_signal.signal.symbol.exchange,
            # currency="USD",
        )

        # Get contract details with retries
        for attempt in range(MAX_RETRIES):
            try:
                self.logger.info(
                    f"Attempting to get contract details ({attempt + 1}/{MAX_RETRIES})"
                )
                details = self.ib_connector.reqContractDetails(contract)
                if details:
                    return details[0]
                else:
                    self.logger.warning("Contract details not found")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                    continue
            except Exception as e:
                self.logger.error(f"Error getting contract details: {str(e)}")
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
            trading_schedule = contract_details.tradingHours
            if not trading_schedule:
                self.logger.warning("No trading hours information available")
                return False
            trading_schedule = self.parse_data(contract_details)

            for day in trading_schedule:
                if day.status == "OPEN":
                    self.logger.info(
                        f"Trading hours open: {day.start} ({day.start.tzname()} UTC{day.start.strftime('%z')}) - "
                        f"{day.end} ({day.end.tzname()} UTC{day.end.strftime('%z')}) "
                        f"now {self.current_time} ({self.current_time.tzname()} UTC{self.current_time.strftime('%z')})"
                    )
                    if self.current_time >= day.start and self.current_time <= day.end:
                        self.logger.info(
                            f"Current time is within trading hours! Session: {day.start} - {day.end}, current time: {self.current_time}"
                        )
                        return True
            return False

        except Exception as e:
            self.logger.error(f"Error checking trading hours: {str(e)}")
            raise (e)
            return False

    def parse_data(self, contract_details) -> list:
        trading_hours = []
        data = contract_details.tradingHours
        tz = contract_details.timeZoneId
        for entry in data.split(";"):
            if not entry.strip():
                continue

            parts = entry.split(":", 1)

            data, status = parts

            if status == "CLOSED":
                trading_hours.append(
                    TradingHours(status="CLOSED", start=None, end=None)
                )
            else:
                data = entry
                start = datetime(
                    year=int(data[0:4]),
                    month=int(data[4:6]),
                    day=int(data[6:8]),
                    hour=int(data[9:11]),
                    minute=int(data[11:13]),
                    tzinfo=pytz.timezone(tz),
                ).astimezone(pytz.UTC)

                end = datetime(
                    year=int(data[14:18]),
                    month=int(data[18:20]),
                    day=int(data[20:22]),
                    hour=int(data[23:25]),
                    minute=int(data[25:27]),
                    tzinfo=pytz.timezone(tz),
                ).astimezone(pytz.UTC)

                trading_hours.append(
                    TradingHours(
                        status="OPEN",
                        start=start,
                        end=end,
                    )
                )
        return trading_hours

    def _open_order(self, signal: BotSeasonalSignal, contract: ContFuture) -> None:
        """Opens an order for the signal"""
        try:
            self.logger.info(
                f"[1] Starting to open order for signal {signal.pk}, contract {contract.symbol}"
            )
            self.logger.info("[2] Requesting historical data...")

            # Get historical data with retries
            bars = self.ib_connector.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr="1 D",
                barSizeSetting="1 min",
                whatToShow="TRADES",
                useRTH=True,
                timeout=HISTORICAL_DATA_TIMEOUT,
            )
            if not bars:
                raise Exception("Failed to get historical data")

            self.logger.info(f"[3] Received historical data: {len(bars)} bars")

            actual_price = float(bars[-1].close)
            self.logger.info(
                f"[4] Calculated current price for {contract.symbol}: {actual_price}"
            )

            parent_id = self.ib_connector.client.getReqId()
            self.logger.info(f"[5] Got parent order ID: {parent_id}")

            entry_action = self.get_entry_direction(signal)
            exit_action = self.get_exit_direction(signal)
            self.logger.info(
                f"[6] Determined directions: entry={entry_action}, exit={exit_action}"
            )

            # Create limit order
            self.logger.info("[7] Creating limit order...")
            limit_order = LimitOrder(
                action=entry_action,
                totalQuantity=1,  # Temporary value
                lmtPrice=actual_price,
                orderId=parent_id,
            )
            limit_order.tif = "GTC"
            limit_order.transmit = False
            # Set activation time
            activation_time = (timezone.now() + timedelta(minutes=5)).strftime(
                "%Y%m%d-%H:%M:%S"
            )
            self.logger.info(f"Order activation time: {repr(activation_time)}")
            # limit_order.goodAfterTime = activation_time
            self.logger.info(f"[8] Set order activation time: {activation_time}")

            # Calculate stop loss
            self.logger.info("[9] Calculating stop loss...")
            stoploss = self.calculate_stoploss(signal, actual_price)
            self.logger.info(f"[10] Calculated stop price: {stoploss}")

            # Calculate position size
            self.logger.info("[11] Calculating position size...")
            balance = float(self.get_balance())
            self.logger.info(f"[12] Got account balance: {balance}")

            lots = self.calculate_position_size(
                balance=balance,
                entry_price=actual_price,
                stop_loss=stoploss,
                multiplier=float(contract.multiplier),
                risk_percent=signal.signal.risk,
            )
            self.logger.info(f"[13] Calculated position size: {lots} contracts")

            # Update order quantity
            limit_order.totalQuantity = lots
            self.logger.info("[14] Updated limit order quantity")

            # Place limit order with retries
            trade = None
            for attempt in range(MAX_RETRIES):
                try:
                    self.logger.info(
                        f"[15] Attempting to place limit order ({attempt + 1}/{MAX_RETRIES})..."
                    )
                    trade = self.ib_connector.placeOrder(contract, limit_order)
                    if trade:
                        break
                except Exception as e:
                    self.logger.error(f"Error placing limit order: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                    continue

            if not trade:
                raise Exception("Failed to place limit order after all attempts")

            self.logger.info(f"[16] Limit order placed, ID: {trade.order.orderId}")

            # Create and place stop order with retries
            self.logger.info("[17] Creating stop order...")
            stop_order = StopOrder(
                action=exit_action,
                totalQuantity=lots,
                stopPrice=stoploss,
            )
            stop_order.parentId = trade.order.orderId
            stop_order.transmit = True
            stop_order.tif = "GTC"
            self.logger.info(
                f"[18] Linking stop order to parent order {trade.order.orderId}"
            )

            stop_trade = None
            for attempt in range(MAX_RETRIES):
                try:
                    self.logger.info(
                        f"[19] Attempting to place stop order ({attempt + 1}/{MAX_RETRIES})..."
                    )
                    stop_trade = self.ib_connector.placeOrder(contract, stop_order)
                    if stop_trade:
                        break
                except Exception as e:
                    self.logger.error(f"Error placing stop order: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                    continue

            if not stop_trade:
                raise Exception("Failed to place stop order after all attempts")

            self.logger.info(f"[20] Stop order placed, ID: {stop_trade.order.orderId}")
            self.ib_connector.sleep(1)

            # Check status
            status = stop_trade.orderStatus.status
            self.logger.info(f"[DEBUG] Stop order status: {status}")

            # Check order logs
            if stop_trade.log:
                for log in stop_trade.log:
                    self.logger.info(f"[DEBUG] Stop order log: {log.message}")

            if trade.order.permId == 0:
                # If permId is still 0, wait for update
                counter = 0
                while trade.order.permId == 0 and counter < 5:
                    self.logger.info(
                        f"Waiting for permId for order {trade.order.orderId}..."
                    )
                    self.ib_connector.sleep(1)  # Wait more
                    counter += 1
            if trade.order.permId == 0:
                self.logger.warning(
                    f"Failed to get permId for order {trade.order.orderId}"
                )
            else:
                logger.info(
                    f"Order placed. orderId: {trade.order.orderId}, permId: {trade.order.permId}"
                )

            # Save order ID in signal
            signal.order_id = trade.order.orderId
            signal.save()
            self.logger.info(
                f"[21] Saved order perm ID {trade.order} in signal {signal.pk}"
            )
            self.logger.info(
                f"[DEBUG] StopOrder -> action={stop_order.action}, "
                f"qty={stop_order.totalQuantity}, stopPrice={stop_order.auxPrice}, "
                f"parentId={stop_order.parentId}, transmit={stop_order.transmit}"
            )
            self.logger.info(
                f"""[22] ORDER PLACEMENT SUMMARY:
            Symbol: {contract.symbol}
            Direction: {entry_action}
            Entry price: {actual_price}
            Stop loss: {stoploss}
            Quantity: {lots}
            Limit order ID: {trade.order.orderId}
            Stop order ID: {stop_trade.order.orderId}
            Activation time: {activation_time}
            """
            )

        except Exception as e:
            self.logger.error(f"[ERROR] Error opening order: {str(e)}", exc_info=True)
            raise

    def get_balance(self) -> float:
        account_summary = self.ib_connector.accountSummary()
        net_liquidation_values = [
            val for val in account_summary if val.tag == "NetLiquidation"
        ]
        for value in net_liquidation_values:
            print(
                f"Account: {value.account}, NetLiquidation: {value.value} {value.currency}"
            )
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
                (
                    actual_price - stoploss_value
                    if is_long
                    else actual_price + stoploss_value
                ),
                2,
            )
        else:
            stop_price = round(
                (
                    actual_price * (1 - stoploss_value / 100)
                    if is_long
                    else actual_price * (1 + stoploss_value / 100)
                ),
                2,
            )
        return stop_price

    def calculate_position_size(
        self,
        balance,
        entry_price,
        stop_loss,
        multiplier: int | float = 1,
        risk_percent=2,
    ):
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
            balance = float(balance)
            entry_price = float(entry_price)
            stop_loss = float(stop_loss)
            multiplier = float(multiplier)
            risk_percent = float(risk_percent)

            self.logger.info("Calculating position size:")
            self.logger.info(f"Balance: {balance}")
            self.logger.info(f"Entry price: {entry_price}")
            self.logger.info(f"Stop loss: {stop_loss}")
            self.logger.info(f"Multiplier: {multiplier}")
            self.logger.info(f"Risk percent: {risk_percent}%")

            risk_amount = balance * (risk_percent / 100)  # Amount of money to risk
            risk_per_unit = (
                abs(entry_price - stop_loss) * multiplier
            )  # Loss per contract

            self.logger.info(f"Risk amount: {risk_amount}")
            self.logger.info(f"Risk per contract: {risk_per_unit}")

            if risk_per_unit == 0:
                self.logger.warning("Risk per contract is 0, returning 1 contract")
                return 1

            quantity = risk_amount / risk_per_unit  # Number of contracts
            result = max(1, int(quantity))  # Minimum 1 contract

            self.logger.info(f"Calculated number of contracts: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            self.logger.info("Returning minimum position size: 1")
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
                f"=== Starting position check for {contract.contract.symbol} ==="
            )

            # 1. Check for open position
            self.logger.info("Checking for open position...")
            positions = self.ib_connector.positions()

            # Log all positions for debugging
            self.logger.info(f"Retrieved {len(positions)} positions:")
            for i, pos in enumerate(positions):
                self.logger.info(
                    f"  #{i+1}: symbol={pos.contract.symbol}, "
                    f"position={pos.position}, "
                    f"avgCost={pos.avgCost}"
                )

            position = next(
                (p for p in positions if p.contract.symbol == contract.contract.symbol),
                None,
            )

            if not position:
                self.logger.warning(
                    f"Position for {contract.contract.symbol} not found in positions list."
                )
                return False

            if position.position == 0:
                self.logger.info(
                    f"Position for {contract.contract.symbol} has zero volume."
                )
                return False

            self.logger.info(
                f"Found position for {contract.contract.symbol}: "
                f"volume={position.position}, average price={position.avgCost}"
            )

            # 2. Check for active stop orders
            self.logger.info("Checking for active stop orders...")
            open_orders = self.ib_connector.openOrders()

            # Log all open orders
            self.logger.info(f"Retrieved {len(open_orders)} open orders:")
            for i, order in enumerate(open_orders[:5]):  # Show first 5 for brevity
                self.logger.info(
                    f"  #{i+1}: orderId={order.orderId}, "
                    f"action={order.action}, "
                    f"orderType={order.orderType}, "
                    f"totalQuantity={order.totalQuantity}"
                )

            # 3. Close position
            self.logger.info(
                f"Preparing to close position for {contract.contract.symbol}"
            )
            action = "SELL" if position.position > 0 else "BUY"
            quantity = abs(position.position)

            self.logger.info(
                f"Creating order: {action} {quantity} {contract.contract.symbol}"
            )

            close_order = MarketOrder(action, quantity)
            close_order.orderId = self.ib_connector.client.getReqId()  # Generate new ID
            self.logger.info(f"Assigned new order ID: {close_order.orderId}")

            trade = self.ib_connector.placeOrder(contract.contract, close_order)

            if not trade:
                self.logger.error(
                    f"Failed to place closing order for {contract.contract.symbol}."
                )
                return False

            self.logger.info(
                f"Closing order placed: orderId={trade.order.orderId}, "
                f"status={trade.orderStatus.status}, "
                f"{action} {quantity} {contract.contract.symbol}"
            )

            # 4. Check closing status
            wait_time = 5  # Increase wait time for order fill
            self.logger.info(
                f"Waiting for closing order execution ({wait_time} sec)..."
            )
            self.ib_connector.sleep(wait_time)

            # Check if position was closed
            positions = self.ib_connector.positions()
            position = next(
                (p for p in positions if p.contract.symbol == contract.contract.symbol),
                None,
            )

            if not position or position.position == 0:
                self.logger.info(
                    f"Position for {contract.contract.symbol} successfully closed"
                )
                return True
            else:
                self.logger.warning(
                    f"Failed to fully close position for {contract.contract.symbol}, "
                    f"remaining volume: {position.position}"
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Error closing position {contract.contract.symbol}: {str(e)}",
                exc_info=True,
            )
            # Log additional error information
            import traceback

            self.logger.error(f"Error details: {traceback.format_exc()}")
            return False
        finally:
            self.logger.info(
                f"=== Finished position check for {contract.contract.symbol} ==="
            )
            self.logger.info("=" * 40)
