import argparse
import itertools
import operator
import os
import sys
import time
from datetime import datetime
from threading import Thread

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5 import QtWidgets
from pyqtgraph import PlotWidget, QtCore, QtGui, plot

import util
from candle import Candle
from chart import Chart
from customtypes import CurrencyPair, TradingMode
from worker import Worker, WorkerStatus


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


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [datetime.utcfromtimestamp(value).strftime("%d/%m/%y %H:%M:%S") for value in values]


class CandlestickItem(pg.GraphicsObject):
    sigPlotChanged = QtCore.Signal(object)

    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data  ## data must have fields: time, open, close, min, max
        self.picture = QtGui.QPicture()
        self.rect_height = 0
        self.rect_start = 0

        self.generatePicture()

    def setData(self, data):
        self.data = data
        self.generatePicture()
        self.informViewBoundsChanged()
        self.sigPlotChanged.emit(self)

    def generatePicture(self):
        if not self.data:
            return

        ## pre-computing a QPicture object allows paint() to run much more quickly,
        ## rather than re-drawing the shapes every time.

        if self.picture is None:
            self.picture = QtGui.QPicture()

        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w'))
        w = (self.data[1][0] - self.data[0][0]) / 3.
        for (t, open, close, low, high) in self.data:

            self.rect_height = [self.rect_height, high][int(not bool(self.rect_height) or high > self.rect_height)]
            self.rect_start = [self.rect_start, low][int(not bool(self.rect_start) or low < self.rect_start)]

            if open > close:
                p.setBrush(pg.mkBrush('#F84960'))
                p.setPen(pg.mkPen('#F84960'))
            else:
                p.setBrush(pg.mkBrush('#02C076'))
                p.setPen(pg.mkPen('#02C076'))

            p.drawLine(QtCore.QPointF(t, low), QtCore.QPointF(t, high))
            p.drawRect(QtCore.QRectF(t - w, open, w * 2, close - open))
        p.end()

    def paint(self, p, *args):
        # print("DRAW")
        # p.drawPicture(0, 0, self.picture)
        self.picture.play(p)

    def boundingRect(self):
        ## boundingRect _must_ indicate the entire area that will be drawn on
        ## or else we will get artifacts and possibly crashing.
        ## (in this case, QPicture does all the work of computing the bouning rect for us)
        rect = QtCore.QRectF(self.picture.boundingRect())
        return QtCore.QRectF(rect.x(), self.rect_start, rect.width(), self.rect_height)


class MainWindow(pg.GraphicsView):
    def __init__(self, args):
        super(MainWindow, self).__init__()

        # Configure Trader
        self.configure_trader(args)

        # Configure main window
        self.setWindowTitle(f"Trader T800: {self.pair}")

        self.layout = pg.GraphicsLayout()
        self.setCentralWidget(self.layout)

        # Configure view
        self.configure_view()

    def closeEvent(self, event):
        self.strategy_ticker_thread.stop()
        self.strategy_ticker_thread.join()
        event.accept()

    def configure_trader(self, args):
        self.pair = CurrencyPair(*args.pair.split(","))
        self.exchange = util.get_exchange_api(args.exchange)
        self.strategies_mgr = util.StrategiesManager("strategies/")

        self.tick = int(args.tick)
        self.backtest_tick = float(args.tick_b)
        self.period = util.interval_mapper(args.period)
        self.preload = int(args.preload)

        self.mode = util.mode_mapper(args.mode)

        self.start_time = int(args.t_start or 0)
        self.start_end = util.end_time(args.t_end or 0)

        self.chart = Chart(self.exchange, self.pair, None)

        strategy = self.strategies_mgr.get_strategy(args.strategy)

        budget = float(args.budget or 0)

        if not budget and self.mode in [TradingMode.LIVE]:
            raise ValueError("Budget should be more that '0' for live trading.")

        self.strategy = strategy(self.mode, budget, self.chart, self.exchange)

        self.strategy_ticker_thread = None

        self.open_trades_candles = []
        self.close_trades_candles = []

    def configure_view(self):
        date_axis1 = TimeAxisItem(orientation='bottom')
        date_axis2 = TimeAxisItem(orientation='bottom')
        date_axis3 = TimeAxisItem(orientation='bottom')

        self.plot_price = self.layout.addPlot(0, 0, title='Price with EMA 50,200', axisItems={'bottom': date_axis1})
        self.plot_rsi = self.layout.addPlot(1, 0, title='RSI', axisItems={'bottom': date_axis2})
        self.plot_dmi = self.layout.addPlot(2, 0, title='DMI', axisItems={'bottom': date_axis3})

        self.plot_price.setXLink(self.plot_rsi)
        self.plot_rsi.setXLink(self.plot_dmi)

        self.plot_price.showGrid(x=True, y=True, alpha=0.3)
        self.plot_rsi.showGrid(x=True, y=True, alpha=0.3)
        self.plot_dmi.showGrid(x=True, y=True, alpha=0.3)

    def main(self):
        interval = util.interval_mapper_to_seconds(self.period)
        start = int(time.time()) - (interval * self.preload)
        end = int(time.time())

        if self.mode in [TradingMode.BACKTEST]:
            start = self.start_time - (interval * self.preload)
            end = self.start_end

        candles = self.exchange.returnChartData(self.pair, self.period, start, end)

        self.chart.reset(candles[:self.preload])
        self.strategy.preload(self.chart.get_candles())

        candles = candles[self.preload:]

        df = self.strategy.get_indicators()

        TIMEDATA = list(map(lambda i: i.astype(int) * 1e-9, np.array(df["Timestamp"])))
        OPEN = np.array(df["Open"])
        CLOSE = np.array(df["Close"])
        HIGH = np.array(df["High"])
        LOW = np.array(df["Low"])
        EMA50 = np.array(df["EMA50"])
        EMA200 = np.array(df["EMA200"])
        RSI = np.array(df["RSI"])
        ADX = np.array(df["ADX"])
        DI_P = np.array(df["DI+"])
        DI_M = np.array(df["DI-"])

        d = list(zip(TIMEDATA, OPEN, CLOSE, LOW, HIGH))

        self.candle_bars = CandlestickItem(d)

        self.candlesticks = self.plot_price.plot()
        self.plot_price.addItem(self.candle_bars)
        self.plot_price.setYRange(min(LOW), max(HIGH))

        self.curve_ema50 = self.plot_price.plot(TIMEDATA, EMA50)
        self.curve_ema200 = self.plot_price.plot(TIMEDATA, EMA200)
        self.curve_rsi = self.plot_rsi.plot(TIMEDATA, RSI)
        self.curve_adx = self.plot_dmi.plot(TIMEDATA, ADX)
        self.curve_di_p = self.plot_dmi.plot(TIMEDATA, DI_P)
        self.curve_di_m = self.plot_dmi.plot(TIMEDATA, DI_M)

        self.scatter_buy = pg.ScatterPlotItem(size=15, brush=pg.mkBrush(0, 0, 255, 255), pen=pg.mkPen('y'), symbol='t1')
        self.scatter_sell = pg.ScatterPlotItem(size=15, brush=pg.mkBrush(255, 0, 0, 255), pen=pg.mkPen('y'), symbol='t')

        self.plot_price.addItem(self.scatter_buy)
        self.plot_price.addItem(self.scatter_sell)

        self.curve_downtrend = self.plot_price.plot()
        self.curve_uptrend = self.plot_price.plot()

        self.curve_downtrend.setPen(pg.mkPen(color=(255, 0, 0), width=3))
        self.curve_uptrend.setPen(pg.mkPen(color=(0, 0, 255), width=3))

        self.curve_ema50.setPen(pg.mkPen(color=(180, 120, 40), width=2))
        self.curve_ema200.setPen(pg.mkPen(color=(40, 150, 40), width=2))
        self.curve_rsi.setPen(pg.mkPen(color=(40, 40, 200), width=1))
        self.curve_adx.setPen(pg.mkPen(color=(255, 0, 0), width=1))
        self.curve_di_p.setPen(pg.mkPen(color=(0, 0, 255), width=1))
        self.curve_di_m.setPen(pg.mkPen(color=(180, 120, 40), width=1))

        if self.mode in [TradingMode.LIVE, TradingMode.LIVE_TEST]:
            self.strategy_ticker_thread = LiveTicker(self)
        else:
            self.strategy_ticker_thread = BacktestTicker(self, candles)

        self.strategy_ticker_thread.start()

    def chart_tick(self, candle):
        p_uptrend, p_downtrend = self.strategy.on_tick(candle)

        # TODO: move to separate method
        for trade in self.strategy.trades:
            if trade.open_candle:
                self.open_trades_candles.append({
                    'pos': [trade.open_candle.timestamp, trade.open_candle.close],
                    'data': 1
                })

            if trade.close_candle:
                self.close_trades_candles.append({
                    'pos': [trade.close_candle.timestamp, trade.close_candle.close],
                    'data': 1
                })

        df = self.strategy.get_indicators()

        TIMEDATA = list(map(lambda i: i.astype(int) * 1e-9, np.array(df["Timestamp"])))
        OPEN = np.array(df["Open"])
        CLOSE = np.array(df["Close"])
        HIGH = np.array(df["High"])
        LOW = np.array(df["Low"])
        EMA50 = np.array(df["EMA50"])
        EMA200 = np.array(df["EMA200"])
        RSI = np.array(df["RSI"])
        ADX = np.array(df["ADX"])
        DI_P = np.array(df["DI+"])
        DI_M = np.array(df["DI-"])

        d = list(zip(TIMEDATA, OPEN, CLOSE, LOW, HIGH))
        self.candle_bars.setData(d)

        self.curve_ema50.setData(TIMEDATA, EMA50)
        self.curve_ema200.setData(TIMEDATA, EMA200)
        self.curve_rsi.setData(TIMEDATA, RSI)
        self.curve_adx.setData(TIMEDATA, ADX)
        self.curve_di_p.setData(TIMEDATA, DI_P)
        self.curve_di_m.setData(TIMEDATA, DI_M)

        self.scatter_sell.setData(spots=self.close_trades_candles)
        self.scatter_buy.setData(spots=self.open_trades_candles)

        t_downtrend = list(TIMEDATA[-len(p_downtrend):])
        t_uptrend = list(TIMEDATA[-len(p_uptrend):])

        self.curve_downtrend.setData(t_downtrend, p_downtrend)
        self.curve_uptrend.setData(t_uptrend, p_uptrend)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('--preload', '-l', default=300, help=f"Num old candles to preload.")

    p.add_argument('--mode', '-m', default='live', help=f"Trading modes (backtest, live_test, live)")
    p.add_argument('--t-start', '-S', default=None, help=f"Timespan start (used for backtesting).")
    p.add_argument('--t-end', '-E', default=None, help=f"Timespan end (used for backtesting).")

    p.add_argument('--pair', '-c', default='BTC,USDT', help=f"Currency pair. ex. BTC,USDT.")
    p.add_argument('--tick', '-t', default=30, help=f"Candle update timespan.")
    p.add_argument('--tick-b', default=0.5, help=f"Candle update time for backtesting.")
    p.add_argument('--budget',
                   '-b',
                   default=None,
                   help=f"Budget used to by crypto in currency which second param in pair.")

    p.add_argument('--period', '-p', default='5m', help=f"Timespan width for candle.")
    p.add_argument('--period-help', '-P', action='store_true', help=f"Show period help.")

    p.add_argument('--exchange', '-e', default=None, help=f"Exchange used for trading.")
    p.add_argument('--strategy', '-s', default='default', help=f"Trading strategy.")

    p.add_argument('--list-exchanges', default=None, help=f"Show available exchanges.")
    p.add_argument('--list-strategies', default=None, help=f"Show available strategies.")

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(p.parse_args())
    w.show()

    w.main()

    sys.exit(app.exec_())
