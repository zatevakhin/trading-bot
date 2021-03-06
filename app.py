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
from workers.websocket_live_ticker import WebsocketLiveTicker

SUPPORT_PEN = pg.mkPen(color='#00AA0070', style=QtCore.Qt.SolidLine, width=2)
RESIST_PEN = pg.mkPen(color='#AA000070', style=QtCore.Qt.SolidLine, width=2)


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

        params = {'level': args.log_level, 'format': format, 'backtrace': True, 'diagnose': True, 'enqueue': False, 'catch': True}

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
        date_axis5 = TimeAxisItem(orientation='bottom')
        date_axis6 = TimeAxisItem(orientation='bottom')

        self.plot_price = self.layout.addPlot(0, 0, title='Price with EMA 50,200', axisItems={'bottom': date_axis1})
        self.plot_rsi = self.layout.addPlot(1, 0, title='RSI', axisItems={'bottom': date_axis2})
        self.plot_dmi = self.layout.addPlot(2, 0, title='DMI', axisItems={'bottom': date_axis3})
        self.plot_scalp = self.layout.addPlot(3, 0, title='Scalping', axisItems={'bottom': date_axis4})
        self.plot_scalp_visibile = True
        self.plot_macd = self.layout.addPlot(4, 0, title='MACD', axisItems={'bottom': date_axis5})
        self.plot_macd_visibile = True
        self.plot_volume = self.layout.addPlot(5, 0, title='VOLUME', axisItems={'bottom': date_axis6})
        self.plot_volume_visibile = True

        # self.horizontal = pg.LinearRegionItem(orientation=pg.LinearRegionItem.Horizontal,
        #                                       movable=False,
        #                                       pen=pg.mkPen(color='#AAAAAA70', style=QtCore.Qt.SolidLine, width=1))

        self.supports = []
        self.resists = []

        self.resistance_1 = self.plot_price.plot(pen=RESIST_PEN)
        self.resistance_2 = self.plot_price.plot(pen=RESIST_PEN)
        self.resistance_3 = self.plot_price.plot(pen=RESIST_PEN)

        # self.support_1 = self.plot_price.plot(pen=SUPPORT_PEN)
        # self.support_2 = self.plot_price.plot(pen=SUPPORT_PEN)
        # self.support_3 = self.plot_price.plot(pen=SUPPORT_PEN)

        # self.plot_price.addItem(self.horizontal)

        self.plot_price.setXLink(self.plot_rsi)
        self.plot_rsi.setXLink(self.plot_dmi)
        self.plot_dmi.setXLink(self.plot_scalp)
        self.plot_scalp.setXLink(self.plot_macd)
        self.plot_macd.setXLink(self.plot_volume)

        self.plot_price.showGrid(x=True, y=True, alpha=0.3)
        self.plot_rsi.showGrid(x=True, y=True, alpha=0.3)
        self.plot_dmi.showGrid(x=True, y=True, alpha=0.3)
        self.plot_scalp.showGrid(x=True, y=True, alpha=0.3)
        self.plot_macd.showGrid(x=True, y=True, alpha=0.3)
        self.plot_volume.showGrid(x=True, y=True, alpha=0.3)
        self.layout.removeItem(self.plot_dmi)
        self.layout.removeItem(self.plot_volume)

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
        volume_list = indicators.volume_array
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

        self.curve_macd = self.plot_macd.plot()
        self.curve_macd_sig = self.plot_macd.plot()
        self.curve_macd_hst = self.plot_macd.plot()

        self.curve_volume = self.plot_volume.plot(datetime_list, volume_list)

        self.scatter_price = pg.ScatterPlotItem()
        self.plot_price.addItem(self.scatter_price)

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

        self.curve_macd.setPen(pg.mkPen(color=(0, 0, 255), width=1))
        self.curve_macd_sig.setPen(pg.mkPen(color=(255, 0, 0), width=1))
        self.curve_macd_hst.setPen(pg.mkPen(color=(0, 255, 0), width=1))
        self.curve_volume.setPen(pg.mkPen(color=(100, 255, 100), width=1))

        if self.mode in [TradingMode.LIVE, TradingMode.LIVE_TEST]:
            self.strategy_ticker_thread = WebsocketLiveTicker(self, last_candle)
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
                open_trades_candles.append({'pos': [trade.open_candle.t_open, trade.open_candle.p_close], 'data': 1})

            if trade and trade.close_candle:
                close_trades_candles.append({'pos': [trade.close_candle.t_open, trade.close_candle.p_close], 'data': 1})

        indicators: 'Indicators' = self.strategy.get_indicators()

        datetime_list = indicators.datetime_array
        open_price_list = indicators.open_array
        close_price_list = indicators.close_array
        high_price_list = indicators.high_array
        low_price_list = indicators.low_array
        volume_list = indicators.volume_array
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

        self.curve_volume.setData(datetime_list, volume_list)

        if "scatter" in ret_data:
            data = []
            for item in ret_data.get("scatter", []):
                data.append({
                    "symbol": item["symbol"],
                    "size": item["size"],
                    "pos": item["pos"],
                    "brush": pg.mkBrush(item.get("color", "#000000")),
                    "pen": pg.mkPen('y'),
                })

            self.scatter_price.setData(data)

        if 'macd' in ret_data:
            macd = ret_data.get('macd')
            signal = ret_data.get('signal')
            hist = ret_data.get('hist')

            t_macd = list(datetime_list[-len(macd):])
            self.curve_macd.setData(t_macd, macd)
            self.curve_macd_sig.setData(t_macd, signal)
            self.curve_macd_hst.setData(t_macd, hist)
        else:
            if self.plot_macd_visibile and self.plot_macd:
                self.layout.removeItem(self.plot_macd)
                self.plot_macd_visibile = False

        if 'uptrend' in ret_data:
            uptrend = ret_data.get('uptrend')
            t_uptrend = list(datetime_list[-len(uptrend):])
            self.curve_uptrend.setData(t_uptrend, uptrend)

        if 'downtrend' in ret_data:
            downtrend = ret_data.get('downtrend')
            t_downtrend = list(datetime_list[-len(downtrend):])
            self.curve_downtrend.setData(t_downtrend, downtrend)

        if 'scalping' in ret_data:
            scalping_line = ret_data.get('scalping')
            t_scalping_line = list(datetime_list[-len(scalping_line):])
            self.curve_scalping_line.setData(t_scalping_line, scalping_line)
        else:
            if self.plot_scalp_visibile and self.plot_scalp:
                self.layout.removeItem(self.plot_scalp)
                self.plot_scalp_visibile = False

        if 'lows' in ret_data:

            lows = []
            for pos in ret_data.get("lows"):
                lows.append({'pos': [pos.get("x"), pos.get("y")], 'data': 1})

            self.scatter_lows.setData(spots=lows)

        if 'highs' in ret_data:

            highs = []
            for pos in ret_data.get("highs"):
                highs.append({'pos': [pos.get("x"), pos.get("y")], 'data': 1})

            self.scatter_highs.setData(spots=highs)

        if 'supports' in ret_data:
            supports = ret_data.get('supports')

            for x in range(0, len(supports)):
                support = supports[x]

                x_axis_data = [support.get("x-start"), support.get("x-end")]
                y_axis_data = [support.get("y")] * 2

                if x >= len(self.supports) or not len(self.supports):
                    plot = self.plot_price.plot(x_axis_data, y_axis_data, pen=SUPPORT_PEN)
                    self.supports.append(plot)
                else:
                    support_plot = self.supports[x]
                    support_plot.setData(x_axis_data, y_axis_data)

        if 'resists' in ret_data:
            resists = ret_data.get('resists')

            for x in range(0, len(resists)):
                support = resists[x]

                x_axis_data = [support.get("x-start"), support.get("x-end")]
                y_axis_data = [support.get("y")] * 2

                if x >= len(self.resists) or not len(self.resists):
                    plot = self.plot_price.plot(x_axis_data, y_axis_data, pen=RESIST_PEN)
                    self.resists.append(plot)
                else:
                    support_plot = self.resists[x]
                    support_plot.setData(x_axis_data, y_axis_data)

        # self.plot_price.plot([pos.get("x-start"), pos.get("x-end")], [pos.get("y")] * 2)
        # self.horizontal2.setData([pos.get("x-start"), pos.get("x-end")], [pos.get("y-high"), pos.get("y-high")])
        # self.horizontal.setRegion([pos.get("y-low"), pos.get("y-high")])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('--preload', '-l', default=300, help=f"Num old candles to preload.")

    p.add_argument('--mode', '-m', default='live', help=f"Trading modes (backtest, live_test, live)")
    p.add_argument('--t-start', '-S', default=None, help=f"Timespan start (used for backtesting).")
    p.add_argument('--t-end', '-E', default=None, help=f"Timespan end (used for backtesting).")

    p.add_argument('--pair', '-c', default='BTC,USDT', help=f"Currency pair. ex. BTC,USDT.")
    p.add_argument('--tick', '-t', default=30, help=f"Candle update timespan.")
    p.add_argument('--tick-b', default=0.5, help=f"Candle update time for backtesting.")
    p.add_argument('--budget', '-b', default=None, help=f"Budget used to by crypto in currency which second param in pair.")

    p.add_argument('--period', '-p', default='5m', help=f"Timespan width for candle.")
    p.add_argument('--period-help', '-P', action='store_true', help=f"Show period help.")

    p.add_argument('--exchange', '-e', default=None, help=f"Exchange used for trading.")
    p.add_argument('--strategy', '-s', default='default', help=f"Trading strategy.")
    p.add_argument('--strategy-args', '-a', default=None, help=f"Trading strategy arguments. ex. 'a=1;b=2'")

    p.add_argument('--list-exchanges', default=None, help=f"Show available exchanges.")

    p.add_argument('--log-store',
                   dest='log_store',
                   default=False,
                   action=argparse.BooleanOptionalAction,
                   help=f"Should logs be saved to files.")
    p.add_argument('--log-dir', type=Path, default=Path(__file__).absolute().parent / "logs", help=f"Path to the logs directory.")
    p.add_argument('--log-level', default='INFO', help=f"Logging level.")
    p.add_argument('--log-extended', '-L', action='store_true', help=f"Show extended logs.")

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(p.parse_args())
    w.show()

    w.main()

    sys.exit(app.exec_())
