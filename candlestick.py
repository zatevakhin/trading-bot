import time
from loguru import logger
from termcolor import colored


class Candlestick(object):
    def __init__(self, period=300, timestamp=None, opn=None, close=None, high=None, low=None, average=None):
        self.current = None
        self.open = opn
        self.close = close
        self.high = high
        self.low = low
        self.timestamp = timestamp or int(time.time())
        self.period = period
        self.average = average

        if not self.average:
            prices = [self.high, self.low, self.close]

            if None not in prices:
                self.average = sum(prices) / 3

    def close_time(self):
        return self.timestamp + self.period


    def tick(self, price):
        self.current = float(price)

        if self.open is None:
            self.open = self.current

        if (self.high is None) or (self.current > self.high):
            self.high = self.current

        if (self.low is None) or (self.current < self.low):
            self.low = self.current

        if time.time() >= (self.timestamp + self.period):
            self.close = self.current
            self.average = (self.high + self.low + self.close) / float(3)

        # print(self)

    def isClosed(self):
        return self.close is not None

    def __repr__(self) -> str:
        return f"<Candlestick [{self.timestamp}] Current: {self.current}, High: {self.high}, Low: {self.low}, Open: {self.open}, Close: {self.close}>"
