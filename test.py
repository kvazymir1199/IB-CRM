from ib_insync import *
from datetime import datetime, timedelta

# Подключаемся к IB
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=124)

# Определяем контракт на ближайший фьючерс
contracts = ib.reqContractDetails(ContFuture('SI',"COMEX" ))
if not contracts:
    raise Exception("❌ Контракт не найден!")
print(f"контракт найден: {contracts[0].contract}")
contract = contracts[0].contract  # Берем ближайший контракт
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='1 min',
    whatToShow='TRADES',
    useRTH=True,
    timeout=10
)
print(bars)
# # Рассчитываем время активации ордера (через 3 минуты)
# activation_time = (datetime.now() + timedelta(seconds=15)).strftime('%Y%m%d %H:%M:%S')

# Создаём рыночный ордер с отложенным временем активации
# limit_order = LimitOrder('BUY', 1,lmtPrice=bars[-1].close)
# id = ib.client.getReqId()
# limit_order.goodAfterTime = activation_time  # Устанавливаем время активации
# limit_order.orderId = id
# # Отправляем ордер
# trade = ib.placeOrder(contract, limit_order)
# stop_loss_price = round(bars[-1].close * 0.98, 2)
# stop_order = StopOrder('SELL', 1, stop_loss_price)
# stop_order.parentId = trade.order.orderId  # Связываем как дочерний ордер
# stop_trade = ib.placeOrder(contract, stop_order)

# # print(f"⏳ Ордер запланирован на {activation_time}")
# #
# # # Ждём исполнения ордера
# # print("🕒 Ожидание исполнения ордера...")
# # while trade.orderStatus.status not in ('Filled', 'Cancelled'):
# #     ib.waitOnUpdate()
# #
# # if trade.orderStatus.status != 'Filled':
# #     raise Exception("❌ Ордер не был исполнен!")
# #
# # # ✅ Правильный способ получить цену входа
# # entry_price = trade.orderStatus.avgFillPrice
# # print(f"✅ Ордер исполнен по цене: {entry_price}")
# #
# # # Устанавливаем стоп-лосс (2% ниже цены входа)


# print(f"✅ Стоп-лосс установлен на {stop_loss_price}")


from ib_insync import *
import time

# Подключение к IB Gateway / TWS
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=121)

# Создание контракта: Micro E-mini S&P 500 futures (MES)
contract = ContFuture(symbol='MES', exchange='CME', currency='USD')  # укажи актуальный expiry
ib.qualifyContracts(contract)[0]

# Настройки ордера
parent_order_id = ib.client.getReqId()

# 1. Родительский лимитный ордер
parent = MarketOrder(
    action='BUY',
    totalQuantity=1,
    lmtPrice=5800,
    orderId=parent_order_id,
    transmit=False
)

# 2. Стоп-лосс ордер (дочерний)
stop = StopOrder(
    action='SELL',
    totalQuantity=1,
    stopPrice=5500,
    parentId=parent_order_id,
    transmit=True
)

# Отправка ордеров
trade_parent = ib.placeOrder(contract, parent)
trade_stop = ib.placeOrder(contract, stop)

# Ожидание появления permanent ID (permId)
print("⏳ Ожидаем подтверждения ордеров...")
while not trade_parent.order.permId or not trade_stop.order.permId:
    ib.sleep(1)
    ib.reqOpenOrders()

print(f"✅ Лимитный ордер размещён: permId={trade_parent.order.permId}")
print(f"✅ Стоп-ордер размещён: permId={trade_stop.order.permId}")

ib.disconnect()