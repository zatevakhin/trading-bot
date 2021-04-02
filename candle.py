import calendar
from datetime import datetime

import util


class Candle(object):
    def __init__(self, interval, timestamp=None, opn=None, close=None, high=None, low=None, average=None):
        self.current = None
        self.open = opn
        self.close = close
        self.high = high
        self.low = low
        self.interval = util.interval_mapper_to_seconds(interval)
        self.average = float(average or 0)

        timestamp_local = calendar.timegm(datetime.utcnow().utctimetuple())
        timestamp_local = timestamp_local - (timestamp_local % self.interval)
        self.timestamp = int(timestamp or timestamp_local)

        if not self.average:
            prices = [self.high, self.low, self.close]

            if None not in prices:
                self.average = sum(prices) / 3

    def tick(self, price):
        self.current = float(price)

        if self.open is None:
            self.open = self.current

        if self.high is None or self.current > self.high:
            self.high = self.current

        if self.low is None or self.current < self.low:
            self.low = self.current

        timestamp_local = calendar.timegm(datetime.utcnow().utctimetuple())
        future_close_time = (self.timestamp + self.interval)

        if timestamp_local >= future_close_time:
            self.close = self.current
            self.average = (self.high + self.low + self.close) / float(3)

    def is_closed(self):
        return self.close is not None

    def __repr__(self) -> str:
        return f"<Candle [{self.timestamp}] Current: {self.current}, High: {self.high}, Low: {self.low}, Open: {self.open}, Close: {self.close}>"
