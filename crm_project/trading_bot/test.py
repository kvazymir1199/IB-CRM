from pprint import pprint

from ib_insync import *

# Подключение к IBKR
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=123)

# Определяем контракт на ближайший фьючерс
contracts = ib.reqContractDetails(ContFuture('SI', 'COMEX', currency='USD'))
if not contracts:
    raise Exception("❌ Контракт не найден!")

contract = contracts[0].contract  # Берем ближайший контракт

# Получаем исторические данные
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='1 min',
    whatToShow='BID_ASK',
    useRTH=True,
    timeout=10
)

# Указываем цену для ордеров
entry_price = bars[-1].close
stop_price = entry_price * 0.80  # Стоп-цена (20% ниже)
#
# Генерируем уникальные ID
parent_id = ib.client.getReqId()
stop_id = ib.client.getReqId()

# Основной лимитный ордер (покупка)
# parent_order = LimitOrder('BUY', 1, entry_price, orderId=parent_id, tif='GTC')

# Защитный стоп-ордер (Stop-Loss)
stop_order = StopOrder('SELL', 1, stopPrice=stop_price, orderId=stop_id,  tif='GTC')

# Размещаем ордера

ib.placeOrder(contract, stop_order)    # Стоп-ордер

# Ждём обновления данных
ib.sleep(2)

# Проверяем статус ордеров
orders = ib.orders()
for order in orders:
    print(f"Order ID: {order.orderId}, Status: {order.action}, Type: {order.orderType}, LmtPrice: {getattr(order, 'lmtPrice', None)}, StopPrice: {getattr(order, 'stopPrice', None)}")

# Отключаемся
ib.disconnect()