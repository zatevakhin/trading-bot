import util


class Candle(object):
    def __init__(self, period, t_open, t_close, p_open=None, p_close=None, p_high=None, p_low=None, volume=None):
        self.current = None
        self.p_open = p_open
        self.p_close = p_close
        self.p_high = p_high
        self.p_low = p_low
        self.volume = volume
        self.period = util.interval_mapper_to_seconds(period)
        self.average = float(0)
        self.t_open = t_open
        self.t_close = t_close

        if not self.average:
            prices = [self.p_high, self.p_low, self.p_close]

            if None not in prices:
                self.average = sum(prices) / 3

    def tick(self, p_open, p_close, p_high, p_low, volume, is_closed):
        self.current = float(p_close)
        self.volume = float(volume)

        if self.p_open is None:
            self.p_open = p_open

        if self.p_high is None or p_high > self.p_high:
            self.p_high = p_high

        if self.p_low is None or p_low < self.p_low:
            self.p_low = p_low

        if is_closed:
            self.p_close = self.current
            self.average = (self.p_high + self.p_low + self.p_close) / float(3)

    def is_closed(self):
        return self.p_close is not None

    def __repr__(self) -> str:
        return f"<Candle [{self.t_open}] Current: {self.current}, High: {self.p_high}, Low: {self.p_low}, Open: {self.p_open}, Close: {self.p_close}>"
