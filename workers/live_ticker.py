import time

from candle import Candle

from .baseworker import Worker, WorkerStatus


class LiveTicker(Worker):
    def __init__(self, window, last_candle=None):
        Worker.__init__(self, name="live-ticker")
        self.window = window
        self.status = WorkerStatus.WORKING
        self.period = window.period
        self.chart = window.chart
        self.tick = window.tick
        self.candle: 'Candle' = last_candle

    def stop(self):
        self.status = WorkerStatus.STOPPED

    def run(self):

        while self.status in [WorkerStatus.WORKING]:
            if not self.candle:
                self.candle = Candle(interval=self.period)

            self.candle.tick(self.chart.getCurrentPrice())

            if self.candle.is_closed():
                self.window.chart_tick(self.candle)
                self.candle = Candle(interval=self.period,
                                     opn=self.candle.current,
                                     high=self.candle.current,
                                     low=self.candle.current)

            for _ in range(self.tick + 1):
                if self.status not in [WorkerStatus.WORKING]:
                    break

                time.sleep(1)
