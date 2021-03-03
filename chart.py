from poloniex import Poloniex
from candlestick import Candlestick
from termcolor import colored

def is_almost_match(a, b, error):
    return abs(a - b) <= error


def getChartData(connection: Poloniex, pair, period, start, end, cache):
    cached = cache.select(pair, period, start, end)

    if cached:
        cached_min = min(cached, key=lambda x: x["timestamp"])
        min_timestamp = cached_min["timestamp"]

        cached_max = max(cached, key=lambda x: x["timestamp"])
        max_timestamp = cached_max["timestamp"]

        is_lower_bound_match = is_almost_match(start, min_timestamp, period)
        is_upper_bound_match = is_almost_match(end, max_timestamp, period)
    else:
        is_lower_bound_match = False
        is_upper_bound_match = False

    if not (is_lower_bound_match and is_upper_bound_match):
        print(colored(">>>", 'red'), f"Cache miss ({is_lower_bound_match}, {is_upper_bound_match})")

        returned = connection.returnChartData(pair, period, start, end)

        for item in returned:
            date = item.get("date")
            high = item.get("high")
            low = item.get("low")
            opn = item.get("open")
            close = item.get("close")

            candlestick = Candlestick(period, date, opn, close, high, low)
            cache.insert(pair, candlestick)

    result = []

    for item in cache.select(pair, period, start, end):
            date = item.get("timestamp")
            high = item.get("high")
            low = item.get("low")
            opn = item.get("open")
            close = item.get("close")

            candlestick = Candlestick(period, date, opn, close, high, low)
            result.append(candlestick)

    return result



class Chart(object):
    def __init__(self, connection: Poloniex, pair):
        self.pair = pair
        self.connection = connection
        self.data = []

    def add(self, cnadlestick: Candlestick):
        self.data.append(cnadlestick)

    def reset(self, data: list[Candlestick]):
        self.data = data

    def getPoints(self):
        return self.data

    def getCurrentPrice(self):
        currentValues = self.connection.returnTicker()
        return currentValues[self.pair]["last"]
