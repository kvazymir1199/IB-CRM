from ib_insync import *

# Подключение к IB Gateway / TWS
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

# 🔎 Укажи нужный permId ордера
target_perm_id = 591145901  # ← сюда свой permId

# Запрашиваем открытые ордера у брокера
ib.reqAllOpenOrders()
ib.sleep(1)  # небольшая пауза для получения данных

# Фильтруем по нужному permId
matching_orders = [
    trade for trade in ib.trades()
    if trade.order.permId == target_perm_id
]

# Выводим результат
if matching_orders:
    for trade in matching_orders:
        print(f"✅ Найден ордер:")
        print(f"  Контракт: {trade.contract.localSymbol}")
        print(f"  Действие: {trade.order.action}")
        print(f"  Кол-во: {trade.order.totalQuantity}")
        print(f"  Цена: {getattr(trade.order, 'lmtPrice', 'N/A')} / стоп: {getattr(trade.order, 'auxPrice', 'N/A')}")
        print(f"  Статус: {trade.orderStatus.status}")
else:
    print(f"❌ Ордер с permId = {target_perm_id} не найден.")

ib.disconnect()