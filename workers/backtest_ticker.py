import time

from .baseworker import Worker, WorkerStatus


class BacktestTicker(Worker):
    def __init__(self, window, candles):
        Worker.__init__(self, name="backtest-ticker")
        self.window = window
        self.candles = candles
        self.status = WorkerStatus.WORKING
        self.tick = window.backtest_tick

    def stop(self):
        self.status = WorkerStatus.STOPPED

    def run(self):
        candle = None

        for candle in self.candles:
            self.window.chart_tick(candle)

            if self.status not in [WorkerStatus.WORKING]:
                break

            time.sleep(self.tick)
