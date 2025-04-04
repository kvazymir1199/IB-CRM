from pprint import pprint

from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=123)

account_summary = ib.accountSummary()
net_liquidation_values = [val for val in account_summary if val.tag == 'NetLiquidation']
account = None
# Выводим данные
for value in net_liquidation_values:
    print(f"Account: {value.account}, NetLiquidation: {value.value} {value.currency}")
    account = value.value
print(account)


# equity = float(account_summary.loc['NetLiquidation', 'value'])  # Общий капитал

def calculate_position_size(balance, entry_price, stop_loss, multiplier: int | float = 1, risk_percent=2):
    risk_amount = balance * (risk_percent / 100)  # Сколько денег рискуем
    risk_per_unit = abs(entry_price - stop_loss) * multiplier  # Убыток на 1 контракт
    quantity = risk_amount / risk_per_unit  # Количество контрактов
    return int(quantity)  # Округляем до целого


contract = ContFuture(symbol='SI', exchange='COMEX', currency="USD")

# Запрашиваем детали контракта
details = ib.reqContractDetails(contract)

if details:
    contract_details = details[0]
    min_tick = contract_details.minTick  # Минимальный шаг цены
    multiplier = contract_details.contract.multiplier  # Размер контракта
    tick_value = float(multiplier) * min_tick  # Стоимость тика
    point_value = float(multiplier)  # Стоимость пункта

    print(f"Минимальный шаг цены (Tick Size): {min_tick}")
    print(f"Размер контракта (Multiplier): {multiplier}")
    print(f"Стоимость одного тика (Tick Value): ${tick_value}")
    print(f"Стоимость одного пункта (Point Value): ${point_value}")
    contracts = calculate_position_size(float(account), 200, 100, float(multiplier), 60)
    print(f"Количество контрактов для риска: {contracts}")
ib.disconnect()
# #Получаем все активные (открытые) ордера
# # open_orders: list[Trade] = ib.reqCompletedOrders(apiOnly=True)
# open_orders:list[Trade] =ib.reqOpenOrders()
# for trade in open_orders:
#     print(f"Символ: {trade.contract.symbol}, "
#           f"Средняя цена: {trade.order.action}")
#
# order_id_to_check = 563
#
# all_trades = ib.trades()
#
# for trade in all_trades:
#     if trade.order.orderId == order_id_to_check:
#         print(f"Ордер {order_id_to_check} найден: {pprint(trade)}")
#         print(f"Статус: {trade.orderStatus.status}")
#         break
# else:
#     print(f"Ордер {order_id_to_check} не найден")
