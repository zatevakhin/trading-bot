from enum import Enum, auto


class OrderStatus(Enum):
    NEW = auto()
    PARTIALLY_FILLED = auto()
    FILLED = auto()
    CANCELED = auto()
    PENDING_CANCEL = auto()
    REJECTED = auto()
    EXPIRED = auto()


class Order:
    def __init__(self, exchange, status: OrderStatus, order_id, price: float, quantity: float):
        self.order_id = order_id
        self.status = status
        self.price = price
        self.quantity = quantity
        self.exchange = exchange

    def is_status(self, status):
        return self.status == status

    def __repr__(self) -> str:
        return f"Buy on {self.exchange}, status: {self.status}, id: {self.order_id}, price: {self.price}, qty: {self.quantity}."
