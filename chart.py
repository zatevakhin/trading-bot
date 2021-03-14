from candle import Candle


class Chart(object):
    def __init__(self, exchange, pair, limit=300):
        self.pair = pair
        self.exchange = exchange
        self.data = []
        self.limit = limit

    def apply_limit(self):
        if not self.limit:
            return

        while len(self.data) > self.limit:
            self.data.pop(0)

    def add(self, candle: Candle):
        self.data.append(candle)
        self.apply_limit()

    def reset(self, data: list[Candle]):
        self.data = data
        self.apply_limit()

    def get_candles(self):
        return self.data

    def getCurrentPrice(self):
        return self.exchange.returnTicker(self.pair)
