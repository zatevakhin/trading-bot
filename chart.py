from poloniex import Poloniex
from candlestick import Candlestick
from termcolor import colored

def is_almost_match(a, b, error):
    return abs(a - b) <= error


# def getChartData(connection: Poloniex, pair, period, start, end):
#         returned = connection.returnChartData(pair, period, start, end)

#         result = []
#         for item in returned:
#             (date, high, low, opn, close) = (item.get("date"), item.get("high"), item.get("low"), item.get("open"), item.get("close"))
#             candlestick = Candlestick(period, date, opn, close, high, low)
#             result.append(candlestick)

#         return result



class Chart(object):
    def __init__(self, connection: Poloniex, pair, limit=300):
        self.pair = pair
        self.connection = connection
        self.data = []
        self.limit = limit

    def apply_limit(self):
        if not self.limit:
            return

        while len(self.data) > self.limit:
            self.data.pop(0)

    def add(self, candle: Candlestick):
        self.data.append(candle)
        self.apply_limit()

    def reset(self, data: list[Candlestick]):
        self.data = data
        self.apply_limit()

    def get_candles(self):
        return self.data

    def getCurrentPrice(self):
        currentValues = self.connection.returnTicker()
        return currentValues[self.pair]["last"]
