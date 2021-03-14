import argparse
import sys
import time

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from candle import Candle
from chart import Chart
from cursor import Cursor
from customtypes import CurrencyPair, TradingMode
from util import StrategiesManager, get_exchange_api, mode_mapper


def end_time(t):
    end_t = 0
    if t in ['now']:
        end_t = int(time.time())
    else:
        end_t = int(t)

    return end_t


class Application:
    def __init__(self, args):
        self.exchanges_list = []
        self.strategies_list = []

        self.pair = CurrencyPair(*args.pair.split(","))
        self.exchange = get_exchange_api(args.exchange)
        self.strategies_mgr = StrategiesManager("strategies/")

        self.tick_time = int(args.tick)
        self.period = int(args.period)
        self.preload = int(args.preload)

        self.mode = mode_mapper(args.mode)

        self.start_time = int(args.t_start or 0)
        self.start_end = end_time(args.t_end or 0)

        self.chart = Chart(self.exchange, self.pair, None)

        strategy = self.strategies_mgr.get_strategy(args.strategy)

        budget = float(args.budget or 0)

        if not budget and self.mode in [TradingMode.LIVE]:
            raise ValueError(
                "Budget should be more that '0' for live trading.")

        self.strategy = strategy(self.mode, budget, self.chart, self.exchange)
        print(args.strategy, self.strategy)

    def run(self):

        if self.mode in [TradingMode.BACKTEST]:
            self.app_backtest()
        else:
            self.app_live()

    def app_backtest(self):

        start = int(self.start_time) - (self.period * self.preload)
        end = int(self.start_end)

        candles = self.exchange.returnChartData(self.pair, self.period, start,
                                                end)
        self.chart.reset(candles[:self.preload])

        candles = candles[self.preload:]

        self.strategy.preload(self.chart.get_candles())

        main_chart = plt.figure(facecolor='gray')

        main_chart_gs = gridspec.GridSpec(ncols=1, nrows=3, figure=main_chart)

        price_axis = main_chart.add_subplot(main_chart_gs[0])
        rsi_axis = main_chart.add_subplot(main_chart_gs[1], sharex=price_axis)
        dmi_axis = main_chart.add_subplot(main_chart_gs[2], sharex=price_axis)

        cur_price = Cursor(price_axis)
        cur_rsi = Cursor(rsi_axis)
        cur_dmi = Cursor(dmi_axis)

        def on_marker_update(evt):
            cur_price.on_mouse_move(evt)
            cur_rsi.on_mouse_move(evt)
            cur_dmi.on_mouse_move(evt)

        main_chart.canvas.set_window_title(str(self.pair))
        main_chart.canvas.mpl_connect('motion_notify_event', on_marker_update)

        price_axis.set_facecolor("black")
        rsi_axis.set_facecolor("black")
        dmi_axis.set_facecolor("black")

        df = self.strategy.get_indicators()

        td = pd.Timedelta('30 min')

        lim_min = pd.to_datetime(np.min(df["Timestamp"] - td))
        lim_max = pd.to_datetime(np.max(df["Timestamp"] + td))
        price_axis.set_xlim(lim_min, lim_max)

        (line_price, ) = price_axis.step(df["Timestamp"],
                                         df["Price.c"],
                                         label='Price close')
        (line_ema50, ) = price_axis.plot(df["Timestamp"],
                                         df["EMA50"],
                                         label='EMA50')
        (line_ema200, ) = price_axis.plot(df["Timestamp"],
                                          df["EMA200"],
                                          label='EMA200')
        price_axis.legend()
        price_axis.grid(color='r', linestyle='--', alpha=0.3)

        (line_rsi, ) = rsi_axis.plot(df["Timestamp"], df["RSI"], label='RSI')

        rsi_axis.legend()
        rsi_axis.grid(color='r', linestyle='--', alpha=0.3)

        (line_adx, ) = dmi_axis.plot(df["Timestamp"], df["ADX"], label='ADX')
        (line_di_p, ) = dmi_axis.plot(df["Timestamp"], df["DI+"], label='DI+')
        (line_di_m, ) = dmi_axis.plot(df["Timestamp"], df["DI-"], label='DI-')

        dmi_axis.legend()
        dmi_axis.grid(color='r', linestyle='--', alpha=0.3)

        open_trades_candles = []
        close_trades_candles = []

        for candle in candles:
            self.strategy.on_tick(candle)

            for trade in self.strategy.trades:
                if trade.open_candle:
                    open_trades_candles.append({
                        'x':
                        pd.to_datetime(trade.open_candle.timestamp, unit='s'),
                        'y':
                        trade.open_candle.close
                    })

                if trade.close_candle:
                    close_trades_candles.append({
                        'x':
                        pd.to_datetime(trade.close_candle.timestamp, unit='s'),
                        'y':
                        trade.close_candle.close
                    })

            df = self.strategy.get_indicators()

            line_price.set_data(np.array(df["Timestamp"]),
                                np.array(df["Price.c"]))

            lim_min = pd.to_datetime(np.min(df["Timestamp"] - td))
            lim_max = pd.to_datetime(np.max(df["Timestamp"] + td))

            line_ema50.set_data(np.array(df["Timestamp"]),
                                np.array(df["EMA50"]))

            line_ema200.set_data(np.array(df["Timestamp"]),
                                 np.array(df["EMA200"]))

            line_rsi.set_data(np.array(df["Timestamp"]), np.array(df["RSI"]))

            line_adx.set_data(np.array(df["Timestamp"]), np.array(df["ADX"]))
            line_di_p.set_data(np.array(df["Timestamp"]), np.array(df["DI+"]))
            line_di_m.set_data(np.array(df["Timestamp"]), np.array(df["DI-"]))

            price_axis.relim()
            price_axis.autoscale_view(True, True, True)

            rsi_axis.relim()
            rsi_axis.autoscale_view(True, True, True)

            dmi_axis.relim()
            dmi_axis.autoscale_view(True, True, True)

        oc_df = pd.DataFrame(open_trades_candles)
        cc_df = pd.DataFrame(close_trades_candles)

        if open_trades_candles:
            price_axis.scatter(oc_df["x"], oc_df["y"], c="green", zorder=10)

        if close_trades_candles:
            price_axis.scatter(cc_df["x"], cc_df["y"], c="red", zorder=10)

        plt.show()

    def app_live(self):

        start = int(time.time()) - (self.period * self.preload)
        end = int(time.time())

        candles = self.exchange.returnChartData(self.pair, self.period, start,
                                                end)

        self.chart.reset(candles[:self.preload])

        # Plot
        plt.ion()

        main_chart = plt.figure(facecolor='gray')
        main_chart_gs = gridspec.GridSpec(ncols=1, nrows=3, figure=main_chart)

        self.strategy.preload(self.chart.get_candles())

        price_axis = main_chart.add_subplot(main_chart_gs[0])
        rsi_axis = main_chart.add_subplot(main_chart_gs[1], sharex=price_axis)
        dmi_axis = main_chart.add_subplot(main_chart_gs[2], sharex=price_axis)

        cur_price = Cursor(price_axis)
        cur_rsi = Cursor(rsi_axis)
        cur_dmi = Cursor(dmi_axis)

        def on_marker_update(evt):
            cur_price.on_mouse_move(evt)
            cur_rsi.on_mouse_move(evt)
            cur_dmi.on_mouse_move(evt)

        main_chart.canvas.set_window_title(str(self.pair))
        main_chart.canvas.mpl_connect('motion_notify_event', on_marker_update)

        # plt.setp(price_axis.get_xticklabels(), rotation=20)
        # plt.setp(rsi_axis.get_xticklabels(), rotation=20)

        df = self.strategy.get_indicators()

        td = pd.Timedelta('30 min')

        lim_min = pd.to_datetime(np.min(df["Timestamp"] - td))
        lim_max = pd.to_datetime(np.max(df["Timestamp"] + td))
        price_axis.set_xlim(lim_min, lim_max)
        rsi_axis.set_xlim(lim_min, lim_max)

        price_axis.set_facecolor("black")
        rsi_axis.set_facecolor("black")
        dmi_axis.set_facecolor("black")

        (line_price, ) = price_axis.step(df["Timestamp"],
                                         df["Price.c"],
                                         label='Price close')
        (line_ema50, ) = price_axis.plot(df["Timestamp"],
                                         df["EMA50"],
                                         label='EMA50')
        (line_ema200, ) = price_axis.plot(df["Timestamp"],
                                          df["EMA200"],
                                          label='EMA200')
        price_axis.legend()
        price_axis.grid(color='r', linestyle='--', alpha=0.3)

        (line_rsi, ) = rsi_axis.plot(df["Timestamp"], df["RSI"], label='RSI')

        rsi_axis.legend()
        rsi_axis.grid(color='r', linestyle='--', alpha=0.3)

        (line_adx, ) = dmi_axis.plot(df["Timestamp"], df["ADX"], label='ADX')
        (line_di_p, ) = dmi_axis.plot(df["Timestamp"], df["DI+"], label='DI+')
        (line_di_m, ) = dmi_axis.plot(df["Timestamp"], df["DI-"], label='DI-')

        dmi_axis.legend()
        dmi_axis.grid(color='r', linestyle='--', alpha=0.3)

        current_candle = None

        while True:
            if not current_candle:
                current_candle = Candle(interval=self.period)

            current_candle.tick(self.chart.getCurrentPrice())

            if current_candle.isClosed():
                self.strategy.on_tick(current_candle)

                current_candle = None

            df = self.strategy.get_indicators()

            line_price.set_data(np.array(df["Timestamp"]),
                                np.array(df["Price.c"]))

            line_ema50.set_data(np.array(df["Timestamp"]),
                                np.array(df["EMA50"]))

            line_ema200.set_data(np.array(df["Timestamp"]),
                                 np.array(df["EMA200"]))

            line_rsi.set_data(np.array(df["Timestamp"]), np.array(df["RSI"]))

            line_adx.set_data(np.array(df["Timestamp"]), np.array(df["ADX"]))
            line_di_p.set_data(np.array(df["Timestamp"]), np.array(df["DI+"]))
            line_di_m.set_data(np.array(df["Timestamp"]), np.array(df["DI-"]))

            price_axis.relim()
            price_axis.autoscale_view(True, True, True)

            rsi_axis.relim()
            rsi_axis.autoscale_view(True, True, True)

            dmi_axis.relim()
            dmi_axis.autoscale_view(True, True, True)

            plt.pause(self.tick_time)


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument('--chart',
                   '-G',
                   action='store_true',
                   help=f"Show GUI chart.")
    p.add_argument('--preload',
                   '-l',
                   default=300,
                   help=f"Num old candles to preload.")

    p.add_argument('--mode',
                   '-m',
                   default='live',
                   help=f"Trading modes (backtest, live_test, live)")
    p.add_argument('--t-start',
                   '-S',
                   default=None,
                   help=f"Timespan start (used for backtesting).")
    p.add_argument('--t-end',
                   '-E',
                   default=None,
                   help=f"Timespan end (used for backtesting).")

    p.add_argument('--pair',
                   '-c',
                   default='BTC,USDT',
                   help=f"Currency pair. ex. BTC,USDT.")
    p.add_argument('--tick', '-t', default=60, help=f"Candle update timespan.")
    p.add_argument(
        '--budget',
        '-b',
        default=None,
        help=f"Budget used to by crypto in currency which second param in pair."
    )

    p.add_argument('--period',
                   '-p',
                   default=300,
                   help=f"Timespan width for candle.")
    p.add_argument('--period-help',
                   '-P',
                   action='store_true',
                   help=f"Show period help.")

    p.add_argument('--exchange',
                   '-e',
                   default=None,
                   help=f"Exchange used for trading.")
    p.add_argument('--strategy',
                   '-s',
                   default='default',
                   help=f"Trading strategy.")

    p.add_argument('--list-exchanges',
                   default=None,
                   help=f"Show available exchanges.")
    p.add_argument('--list-strategies',
                   default=None,
                   help=f"Show available strategies.")

    app = Application(p.parse_args())
    app.run()


if __name__ == "__main__":
    main(sys.argv[1:])
