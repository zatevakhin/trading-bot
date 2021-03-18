import math

from basetypes.exchange import Exchange
from basetypes.order import Order, OrderStatus
from termcolor import colored


def map_order_status(status):
    return {
        OrderStatus.NEW.name: OrderStatus.NEW,
        OrderStatus.PARTIALLY_FILLED.name: OrderStatus.PARTIALLY_FILLED,
        OrderStatus.FILLED.name: OrderStatus.FILLED,
        OrderStatus.CANCELED.name: OrderStatus.CANCELED,
        OrderStatus.PENDING_CANCEL.name: OrderStatus.PENDING_CANCEL,
        OrderStatus.REJECTED.name: OrderStatus.REJECTED,
        OrderStatus.EXPIRED.name: OrderStatus.EXPIRED,
    }.get(status)


def convert_binance_to_internal(order: dict):
    print(colored(">>>", 'yellow'), order)
    order_id = order.get("orderId")
    order_status = order.get("status")

    fills = order.get("fills", [])
    price = float(order.get("price", 0))

    qty = sum(map(lambda tx: float(tx["qty"]), fills))

    if math.isclose(price, 0):
        price = sum(map(lambda tx: float(tx["price"]), fills)) / len(fills)

    status = map_order_status(order_status)

    return Order(Exchange.BINANCE, status, order_id, price, qty)
