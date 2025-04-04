from ib_insync import IB, MarketOrder, ExecutionFilter
from datetime import datetime
from ib_insync import *




def check_and_close_position(ib: IB, order_id: int, symbol: str):
    # 1. Получить список всех исполнений
    filter = ExecutionFilter()
    executions = ib.reqExecutions(filter)
    #print(executions)

    order_executed = any(exe.execution.orderId == order_id for exe in executions)
    if not order_executed:
        print(f"Order {order_id} не был исполнен.")
        return

    # 3. Получить текущие позиции
    positions = ib.positions()
    position = next((p for p in positions if p.contract.symbol == symbol), None)
    if not position or position.position == 0:
        print(f"Позиция по {symbol} отсутствует или уже закрыта.")
        return

    # 4. Проверить, был ли исполнен Stop-ордер, связанный с order_id
    stop_order_executed = False
    for exe in executions:
        execn = exe.execution
        if execn.orderId != order_id and execn.parentId == order_id:
            if execn.side in ('SLD', 'BOT'):  # можно расширить
                stop_order_executed = True
                break

    if stop_order_executed:
        print(f"Позиция по {symbol} была закрыта стоп-ордером.")
        return

    # 5. Закрываем позицию вручную
    action = 'SELL' if position.position > 0 else 'BUY'
    quantity = abs(position.position)
    contract = position.contract
    close_order = MarketOrder(action, quantity)

    trade = ib.placeOrder(contract, close_order)
    print(f"Позиция по {symbol} закрывается вручную: {action} {quantity}")
    ib.sleep(1)  # Подождем подтверждения


if __name__ == "__main__":
    ib = IB()
    ib.connect('127.0.0.1', 4002, clientId=123)

    check_and_close_position(ib, 779, 'YW')