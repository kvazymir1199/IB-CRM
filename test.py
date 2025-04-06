from ib_insync import *
from datetime import datetime, timedelta

# Подключаемся к IB
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=124)

# Определяем контракт на ближайший фьючерс
contracts = ib.reqContractDetails(ContFuture('ZL',"CBOT" ))
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
# Рассчитываем время активации ордера (через 3 минуты)
activation_time = (datetime.now() + timedelta(seconds=15)).strftime('%Y%m%d %H:%M:%S')

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