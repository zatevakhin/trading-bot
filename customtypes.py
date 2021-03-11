from enum import Enum, auto


class CurrencyPair:
    def __init__(self, buy, sell):
        self.buy = buy
        self.sell = sell

    def fmt_binance(self):
        return f"{self.buy}{self.sell}"

    def fmt_poloniex(self):
        return f"{self.sell}_{self.buy}"

class TradeStatus(Enum):
    OPEN = auto()
    CLOSED = auto()
