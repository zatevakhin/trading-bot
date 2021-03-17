import time

from candle import Candle

from .baseworker import Worker, WorkerStatus


class LiveTicker(Worker):
    def __init__(self, window):
        Worker.__init__(self, name="live-ticker")
        self.window = window
        self.status = WorkerStatus.WORKING
        self.period = window.period
        self.chart = window.chart
        self.tick = window.tick

    def stop(self):
        self.status = WorkerStatus.STOPPED

    def run(self):
        candle = None

        while self.status in [WorkerStatus.WORKING]:
            if not candle:
                candle = Candle(interval=self.period)

            candle.tick(self.chart.getCurrentPrice())

            if candle.is_closed():
                self.window.chart_tick(candle)
                candle = Candle(interval=self.period, opn=candle.current, high=candle.current, low=candle.current)

            for _ in range(self.tick + 1):
                if self.status not in [WorkerStatus.WORKING]:
                    break

                time.sleep(1)
