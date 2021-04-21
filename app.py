import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import pyqtgraph as pg
from loguru import logger
from PyQt5 import QtWidgets
from pyqtgraph import QtCore, QtGui

import util
from chart import Chart
from customtypes import CurrencyPair, TradingMode
from exchange_api import get_exchange_api
from utils.strategy_manager import StrategyManager
from workers.backtest_ticker import BacktestTicker
from workers.baseworker import WorkerStatus
from workers.live_ticker import LiveTicker
from workers.websocket_live_ticker import WebsocketLiveTicker


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
        # p.drawPicture(0, 0, self.picture)
        self.picture.play(p)

    def boundingRect(self):
        ## boundingRect _must_ indicate the entire area that will be drawn on
        ## or else we will get artifacts and possibly crashing.
        ## (in this case, QPicture does all the work of computing the bouning rect for us)
        rect = QtCore.QRectF(self.picture.boundingRect())
        return QtCore.QRectF(rect.x(), self.rect_start, rect.width(), self.rect_height)


class MainWindow(pg.GraphicsView):
    keyPressed = QtCore.Signal(object)

    def __init__(self, args):
        super(MainWindow, self).__init__()
        self.keyPressed.connect(self.on_key)

        # Configure Logger
        self.configure_logger(args)

        # Configure Trader
        self.configure_trader(args)

        # Configure main window
        self.setWindowTitle(f"Trader T800: {self.pair}")
        self.setWindowIcon(QtGui.QIcon('resources/icon.png'))

        self.layout = pg.GraphicsLayout()
        self.setCentralWidget(self.layout)

        # Configure view
        self.configure_view()

        # TODO: Add proxy
        # self.proxy_switcher = ProxySwitcher(PROXY_LIST, 600)
        # self.proxy_switcher.start()

    def keyPressEvent(self, event):
        super(MainWindow, self).keyPressEvent(event)
        self.keyPressed.emit(event)

    def on_key(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            status = self.strategy_ticker_thread.get_status()

            if status == WorkerStatus.WORKING:
                self.strategy_ticker_thread.pause()
            else:
                self.strategy_ticker_thread.resume()
        elif event.key() == QtCore.Qt.Key_O:
            self.strategy.open_trade(stop_loss_percent=1)
        elif event.key() == QtCore.Qt.Key_C:
            self.strategy.close_trade()
        elif event.key() == QtCore.Qt.Key_Q:
            pass
            # self.close()
        elif event.key() == QtCore.Qt.Key_T:
            self.strategy.show_positions()
            # self.close()

    def closeEvent(self, event):
        self.strategy_ticker_thread.stop()
        self.strategy_ticker_thread.join()

        # self.proxy_switcher.stop()
        # self.proxy_switcher.join()

        event.accept()

    def configure_logger(self, args):
        logger.remove()

        save_to_file = args.log_store
        extended_logs = args.log_extended

        if extended_logs:
            format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
        else:
            format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | <level>{message}</level>'

        params = {
            'level': args.log_level,
            'format': format,
            'backtrace': True,
            'diagnose': True,
            'enqueue': False,
            'catch': True
        }

        logger.add(sys.stderr, **params)
        if save_to_file:
            current_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            log_path = args.log_dir / f"START_{current_time}::.txt"
            logger.add(str(log_path), rotation="100 MB", **params)

    def configure_trader(self, args):
        self.pair = CurrencyPair(*args.pair.split(","))
        self.exchange = get_exchange_api(args.exchange)
        self.strategies_mgr = StrategyManager("strategies/")

        self.tick = int(args.tick)
        self.backtest_tick = float(args.tick_b)
        self.period = util.interval_mapper(args.period)
        self.preload = int(args.preload)
        self.websocket = args.websocket

        self.mode = util.mode_mapper(args.mode)

        self.start_time = int(args.t_start or 0)
        self.start_end = util.end_time(args.t_end or 0)

        self.chart = Chart(self.exchange, self.pair, None)

        strategy = self.strategies_mgr.get_strategy(args.strategy)

        budget = float(args.budget or 0)

        if not budget and self.mode in [TradingMode.LIVE]:
            raise ValueError("Budget should be more that '0' for live trading.")

        strategy_args = util.parse_strategy_args(args.strategy_args)
        self.strategy = strategy(strategy_args, self.chart, self.exchange, self.mode, budget)

        self.strategy_ticker_thread = None

    def configure_view(self):
        date_axis1 = TimeAxisItem(orientation='bottom')
        date_axis2 = TimeAxisItem(orientation='bottom')
        date_axis3 = TimeAxisItem(orientation='bottom')
        date_axis4 = TimeAxisItem(orientation='bottom')

        self.plot_price = self.layout.addPlot(0, 0, title='Price with EMA 50,200', axisItems={'bottom': date_axis1})
        self.plot_rsi = self.layout.addPlot(1, 0, title='RSI', axisItems={'bottom': date_axis2})
        self.plot_dmi = self.layout.addPlot(2, 0, title='DMI', axisItems={'bottom': date_axis3})
        self.plot_scalp = self.layout.addPlot(3, 0, title='Scalping', axisItems={'bottom': date_axis4})

        self.plot_price.setXLink(self.plot_rsi)
        self.plot_rsi.setXLink(self.plot_dmi)
        self.plot_dmi.setXLink(self.plot_scalp)

        self.plot_price.showGrid(x=True, y=True, alpha=0.3)
        self.plot_rsi.showGrid(x=True, y=True, alpha=0.3)
        self.plot_dmi.showGrid(x=True, y=True, alpha=0.3)
        self.plot_scalp.showGrid(x=True, y=True, alpha=0.3)

    def main(self):
        interval = util.interval_mapper_to_seconds(self.period)
        start = int(time.time()) - (interval * self.preload)
        end = int(time.time())

        if self.mode in [TradingMode.BACKTEST]:
            start = self.start_time - (interval * self.preload)
            end = self.start_end

        candles, last_candle = self.exchange.returnChartData(self.pair, self.period, start, end)
        self.strategy.on_preload(candles, self.preload)

        candles = candles[self.preload:]

        indicators: 'Indicators' = self.strategy.get_indicators()

        datetime_list = indicators.datetime_array
        open_price_list = indicators.open_array
        close_price_list = indicators.close_array
        high_price_list = indicators.high_array
        low_price_list = indicators.low_array
        ema6_list = indicators.ema6_array
        ema12_list = indicators.ema12_array
        ema25_list = indicators.ema25_array
        ema50_list = indicators.ema50_array
        ema200_list = indicators.ema200_array
        psar_list = indicators.psar_array
        rsi_list = indicators.rsi_array
        adx_list = indicators.adx_array
        di_plus_list = indicators.di_plus_array
        di_minus_list = indicators.di_minus_array

        d = list(zip(datetime_list, open_price_list, close_price_list, low_price_list, high_price_list))

        self.candle_bars = CandlestickItem(d)

        self.candlesticks = self.plot_price.plot()
        self.plot_price.addItem(self.candle_bars)
        self.plot_price.setYRange(min(low_price_list), max(high_price_list))
        self.plot_price.setXRange(min(datetime_list), max(datetime_list))

        self.curve_ema6 = self.plot_price.plot(datetime_list, ema6_list)
        self.curve_ema12 = self.plot_price.plot(datetime_list, ema12_list)
        self.curve_ema25 = self.plot_price.plot(datetime_list, ema25_list)
        self.curve_ema50 = self.plot_price.plot(datetime_list, ema50_list)
        self.curve_ema200 = self.plot_price.plot(datetime_list, ema200_list)
        self.curve_psar = self.plot_price.plot(datetime_list, psar_list)

        self.curve_rsi = self.plot_rsi.plot(datetime_list, rsi_list)
        self.curve_adx = self.plot_dmi.plot(datetime_list, adx_list)
        self.curve_di_p = self.plot_dmi.plot(datetime_list, di_plus_list)
        self.curve_di_m = self.plot_dmi.plot(datetime_list, di_minus_list)

        self.scatter_buy = pg.ScatterPlotItem(size=15, brush=pg.mkBrush(0, 0, 255, 255), pen=pg.mkPen('y'), symbol='t1')
        self.scatter_sell = pg.ScatterPlotItem(size=15, brush=pg.mkBrush(255, 0, 0, 255), pen=pg.mkPen('y'), symbol='t')

        self.plot_price.addItem(self.scatter_buy)
        self.plot_price.addItem(self.scatter_sell)

        self.curve_downtrend = self.plot_price.plot()
        self.curve_uptrend = self.plot_price.plot()
        self.curve_downtrend.setPen(pg.mkPen(color=(255, 0, 0), width=3))
        self.curve_uptrend.setPen(pg.mkPen(color=(0, 0, 255), width=3))

        self.curve_scalping_line = self.plot_scalp.plot()

        self.curve_ema6.setPen(pg.mkPen(color=(255, 0, 255), width=2))
        self.curve_ema12.setPen(pg.mkPen(color=(180, 0, 180), width=2))
        self.curve_ema25.setPen(pg.mkPen(color=(180, 0, 80), width=2))
        self.curve_ema50.setPen(pg.mkPen(color=(180, 120, 40), width=2))
        self.curve_ema200.setPen(pg.mkPen(color=(40, 150, 40), width=2))
        self.curve_rsi.setPen(pg.mkPen(color=(40, 40, 200), width=1))
        self.curve_adx.setPen(pg.mkPen(color=(255, 0, 0), width=1))
        self.curve_di_p.setPen(pg.mkPen(color=(0, 0, 255), width=1))
        self.curve_di_m.setPen(pg.mkPen(color=(180, 120, 40), width=1))

        if self.mode in [TradingMode.LIVE, TradingMode.LIVE_TEST]:
            if self.websocket:
                self.strategy_ticker_thread = WebsocketLiveTicker(self, last_candle)
            else:
                self.strategy_ticker_thread = LiveTicker(self, last_candle)
        else:
            self.strategy_ticker_thread = BacktestTicker(self, candles)

        self.strategy_ticker_thread.start()

    def chart_tick(self, candle):
        ret_data = self.strategy.on_tick(candle)

        # # TODO: move to separate method

        open_trades_candles = []
        close_trades_candles = []

        closed_positions = self.strategy.get_closed_positions()
        open_position = self.strategy.get_open_position()

        for trade in [*closed_positions, open_position]:
            if trade and trade.open_candle:
                open_trades_candles.append({'pos': [trade.open_candle.timestamp, trade.open_candle.close], 'data': 1})

            if trade and trade.close_candle:
                close_trades_candles.append({
                    'pos': [trade.close_candle.timestamp, trade.close_candle.close],
                    'data': 1
                })

        indicators: 'Indicators' = self.strategy.get_indicators()

        datetime_list = indicators.datetime_array
        open_price_list = indicators.open_array
        close_price_list = indicators.close_array
        high_price_list = indicators.high_array
        low_price_list = indicators.low_array
        ema6_list = indicators.ema6_array
        ema12_list = indicators.ema12_array
        ema25_list = indicators.ema25_array
        ema50_list = indicators.ema50_array
        ema200_list = indicators.ema200_array
        psar_list = indicators.psar_array
        rsi_list = indicators.rsi_array
        adx_list = indicators.adx_array
        di_plus_list = indicators.di_plus_array
        di_minus_list = indicators.di_minus_array

        d = list(zip(datetime_list, open_price_list, close_price_list, low_price_list, high_price_list))
        self.candle_bars.setData(d)

        self.curve_ema6.setData(datetime_list, ema6_list)
        self.curve_ema12.setData(datetime_list, ema12_list)
        self.curve_ema25.setData(datetime_list, ema25_list)
        self.curve_ema50.setData(datetime_list, ema50_list)
        self.curve_ema200.setData(datetime_list, ema200_list)
        self.curve_psar.setData(datetime_list, psar_list)
        self.curve_rsi.setData(datetime_list, rsi_list)
        self.curve_adx.setData(datetime_list, adx_list)
        self.curve_di_p.setData(datetime_list, di_plus_list)
        self.curve_di_m.setData(datetime_list, di_minus_list)

        self.scatter_sell.setData(spots=close_trades_candles)
        self.scatter_buy.setData(spots=open_trades_candles)

        if 'uptrend' in ret_data:
            uptrend = ret_data.get('uptrend')
            t_uptrend = list(datetime_list[-len(uptrend):])
            self.curve_uptrend.setData(t_uptrend, uptrend)

        if 'downtrend' in ret_data:
            downtrend = ret_data.get('downtrend')
            t_downtrend = list(datetime_list[-len(downtrend):])
            self.curve_downtrend.setData(t_downtrend, downtrend)

        if 'scalping-line' in ret_data:
            scalping_line = ret_data.get('scalping-line')
            t_scalping_line = list(datetime_list[-len(scalping_line):])
            self.curve_scalping_line.setData(t_scalping_line, scalping_line)
        else:
            if self.plot_scalp:
                self.layout.removeItem(self.plot_scalp)
                self.plot_scalp = None


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
    p.add_argument('--websocket', '-w', action='store_true', help=f"Use websocket to update candle.")

    p.add_argument('--exchange', '-e', default=None, help=f"Exchange used for trading.")
    p.add_argument('--strategy', '-s', default='default', help=f"Trading strategy.")
    p.add_argument('--strategy-args', '-a', default=None, help=f"Trading strategy arguments. ex. 'a=1;b=2'")

    p.add_argument('--list-exchanges', default=None, help=f"Show available exchanges.")

    p.add_argument('--log-store',
                   dest='log_store',
                   default=False,
                   action=argparse.BooleanOptionalAction,
                   help=f"Should logs be saved to files.")
    p.add_argument('--log-dir',
                   type=Path,
                   default=Path(__file__).absolute().parent / "logs",
                   help=f"Path to the logs directory.")
    p.add_argument('--log-level', default='INFO', help=f"Logging level.")
    p.add_argument('--log-extended', '-L', action='store_true', help=f"Show extended logs.")

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(p.parse_args())
    w.show()

    w.main()

    sys.exit(app.exec_())
