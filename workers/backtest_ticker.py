import time

from .baseworker import Worker, WorkerStatus


class BacktestTicker(Worker):
    def __init__(self, window, candles):
        Worker.__init__(self, name="backtest-ticker")
        self.window = window
        self.candles = candles
        self.status = WorkerStatus.WORKING
        self.tick = window.backtest_tick

    def get_status(self):
        return self.status

    def stop(self):
        self.status = WorkerStatus.STOPPED

    def pause(self):
        self.status = WorkerStatus.PAUSED

    def resume(self):
        self.status = WorkerStatus.WORKING

    def run(self):
        candle = None

        for candle in self.candles:

            while self.status in [WorkerStatus.PAUSED]:
                time.sleep(self.tick)

            self.window.chart_tick(candle)

            if self.status not in [WorkerStatus.WORKING]:
                break

            time.sleep(self.tick)
