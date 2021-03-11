from util import get_exchange_api
from customtypes import CurrencyPair

from chart import Chart
from strategy import Strategy
from candle import Candle
from cursor import Cursor

import argparse
import time
import sys

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd



class Application:

    def __init__(self, args):
        self.exchanges_list = []
        self.strategies_list = []

        self.pair = CurrencyPair(*args.pair.split(","))
        self.exchange = get_exchange_api(args.exchange)

        self.tick_time = int(args.tick)
        self.period = int(args.period)
        self.preload = int(args.preload)
        self.backtest = bool(args.backtest)

        self.chart = Chart(self.exchange, self.pair, None)
        self.strategy = Strategy(self.chart, self.exchange)


    def run(self):

        if self.backtest:
            self.app_backtest()
        else:
            self.app_live()


    def app_backtest(self):
        start = int(time.time()) - (self.period * (self.preload * 3))
        end = int(time.time())

        candles = self.exchange.returnChartData(self.pair, self.period, start, end)
        self.chart.reset(candles[:self.preload])

        candles = candles[self.preload:]


        data_list = []
        self.strategy.set_dataframe(data_list)
        self.strategy.preload(self.chart.get_candles())

        # Plot
        # plt.ion()

        main_chart = plt.figure(facecolor='gray')


        main_chart_gs = gridspec.GridSpec(ncols=1, nrows=3, figure=main_chart)

        price_axis = main_chart.add_subplot(main_chart_gs[0])
        macd_axis = main_chart.add_subplot(main_chart_gs[1], sharex=price_axis)
        rsi_axis = main_chart.add_subplot(main_chart_gs[2], sharex=price_axis)

        cur_price = Cursor(price_axis)
        cur_macd = Cursor(macd_axis)
        cur_rsi = Cursor(rsi_axis)

        def on_marker_update(evt):
            cur_price.on_mouse_move(evt)
            cur_macd.on_mouse_move(evt)
            cur_rsi.on_mouse_move(evt)

        main_chart.canvas.mpl_connect('motion_notify_event', on_marker_update)


        price_axis.set_facecolor("black")
        macd_axis.set_facecolor("black")
        rsi_axis.set_facecolor("black")

        df = self.strategy.get_indicators()

        td = pd.Timedelta('30 min')

        lim_min = pd.to_datetime(np.min(df["Timestamp"] - td))
        lim_max = pd.to_datetime(np.max(df["Timestamp"] + td))
        price_axis.set_xlim(lim_min, lim_max)

        (line_price, ) = price_axis.plot(df["Timestamp"], df["Price"], label='Price')
        (line_ema50, ) = price_axis.plot(df["Timestamp"], df["EMA50"], label='EMA50')
        (line_ema200, ) = price_axis.plot(df["Timestamp"], df["EMA200"], label='EMA200')
        price_axis.legend()
        price_axis.grid(color='r', linestyle='--', alpha=0.3)

        (line_macd, ) = macd_axis.plot(df["Timestamp"], df["MACD"], label='MACD')
        (line_macds, ) = macd_axis.plot(df["Timestamp"], df["MACDs"], label='MACDs')

        macd_axis.legend()
        macd_axis.grid(color='r', linestyle='--', alpha=0.3)

        (line_rsi, ) = rsi_axis.plot(df["Timestamp"], df["RSI"], label='RSI')

        rsi_axis.legend()
        rsi_axis.grid(color='r', linestyle='--', alpha=0.3)


        open_trades_candles = []
        close_trades_candles = []

        for candle in candles:
            self.strategy.tick(candle)
            self.chart.add(candle)

            for trade in self.strategy.trades:
                if trade.open_candle:
                    open_trades_candles.append({
                        'x': pd.to_datetime(trade.open_candle.timestamp, unit='s'),
                        'y': trade.open_candle.close
                    })

                if trade.close_candle:
                    close_trades_candles.append({
                        'x': pd.to_datetime(trade.close_candle.timestamp, unit='s'),
                        'y': trade.close_candle.close
                    })


            df = self.strategy.get_indicators()

            line_price.set_data(np.array(df["Timestamp"]), np.array(df["Price"]))

            lim_min = pd.to_datetime(np.min(df["Timestamp"] - td))
            lim_max = pd.to_datetime(np.max(df["Timestamp"] + td))

            line_ema50.set_data(np.array(df["Timestamp"]), np.array(df["EMA50"]))

            line_ema200.set_data(np.array(df["Timestamp"]), np.array(df["EMA200"]))

            line_macd.set_data(np.array(df["Timestamp"]), np.array(df["MACD"]))

            line_macds.set_data(np.array(df["Timestamp"]), np.array(df["MACDs"]))

            line_rsi.set_data(np.array(df["Timestamp"]), np.array(df["RSI"]))

            price_axis.set_xlim(lim_min, lim_max)
            macd_axis.set_xlim(lim_min, lim_max)
            rsi_axis.set_xlim(lim_min, lim_max)

            # plt.pause(self.tick_time)

        oc_df = pd.DataFrame(open_trades_candles)
        cc_df = pd.DataFrame(close_trades_candles)

        if open_trades_candles:
            price_axis.scatter(oc_df["x"], oc_df["y"], c="green")

        if close_trades_candles:
            price_axis.scatter(cc_df["x"], cc_df["y"], c="red")


        plt.show()


    def app_live(self):

        start = int(time.time()) - (self.period * self.preload)
        end = int(time.time())

        candles = self.exchange.returnChartData(self.pair, self.period, start, end)
        self.chart.reset(candles[:self.preload])

        # Plot
        plt.ion()

        main_chart = plt.figure(facecolor='gray')
        main_chart_gs = gridspec.GridSpec(ncols=1, nrows=3, figure=main_chart)

        data_list = []
        self.strategy.set_dataframe(data_list)
        self.strategy.preload(self.chart.get_candles())

        price_axis = main_chart.add_subplot(main_chart_gs[0])
        rsi_axis = main_chart.add_subplot(main_chart_gs[1], sharex=price_axis)

        cur_price = Cursor(price_axis)
        cur_rsi = Cursor(rsi_axis)

        def on_marker_update(evt):
            cur_price.on_mouse_move(evt)
            cur_rsi.on_mouse_move(evt)

        main_chart.canvas.mpl_connect('motion_notify_event', on_marker_update)

        plt.setp(price_axis.get_xticklabels(), rotation=20)
        plt.setp(rsi_axis.get_xticklabels(), rotation=20)

        df = self.strategy.get_indicators()

        td = pd.Timedelta('30 min')

        lim_min = pd.to_datetime(np.min(df["Timestamp"] - td))
        lim_max = pd.to_datetime(np.max(df["Timestamp"] + td))
        price_axis.set_xlim(lim_min, lim_max)
        rsi_axis.set_xlim(lim_min, lim_max)

        price_axis.set_facecolor("black")
        rsi_axis.set_facecolor("black")


        (line_price, ) = price_axis.step(df["Timestamp"], df["Price"], label='Price')
        (line_ema50, ) = price_axis.plot(df["Timestamp"], df["EMA50"], label='EMA50')
        (line_ema200, ) = price_axis.plot(df["Timestamp"], df["EMA200"], label='EMA200')
        price_axis.legend()
        price_axis.grid(color='r', linestyle='--', alpha=0.3)

        (line_rsi, ) = rsi_axis.plot(df["Timestamp"], df["RSI"], label='RSI')

        rsi_axis.legend()
        rsi_axis.grid(color='r', linestyle='--', alpha=0.3)

        current_candle = Candle(period=self.period)

        while True:
            current_candle.tick(self.chart.getCurrentPrice())

            if current_candle.isClosed():
                self.chart.add(current_candle)
                self.strategy.tick(current_candle)

                current_candle = Candle(period=self.period)

            df = self.strategy.get_indicators()

            line_price.set_data(np.array(df["Timestamp"]), np.array(df["Price"]))

            line_ema50.set_data(np.array(df["Timestamp"]), np.array(df["EMA50"]))

            line_ema200.set_data(np.array(df["Timestamp"]), np.array(df["EMA200"]))

            line_rsi.set_data(np.array(df["Timestamp"]), np.array(df["RSI"]))

            price_axis.relim()
            price_axis.autoscale_view(True, True, True)

            rsi_axis.relim()
            rsi_axis.autoscale_view(True, True, True)

            plt.pause(self.tick_time)


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument('--chart', '-G', action='store_true', help=f"Show GUI chart.")
    p.add_argument('--preload', '-l', default=300, help=f"Num old candles to preload.")

    p.add_argument('--backtest', '-T', action='store_true', default=False, help=f"Backtest mode.")
    p.add_argument('--t-start', '-S', default=None, help=f"Timespan start (used for backtesting).")
    p.add_argument('--t-end', '-E', default=None, help=f"Timespan end (used for backtesting).")

    p.add_argument('--pair', '-c', default='USDT_BTC', help=f"Currency pair.")
    p.add_argument('--tick', '-t', default=30, help=f"Candle update timespan.")

    p.add_argument('--period', '-p', default=300, help=f"Timespan width for candle.")
    p.add_argument('--period-help', '-P', action='store_true', help=f"Show period help.")

    p.add_argument('--exchange', '-e', default=None, help=f"Exchange used for trading.")
    p.add_argument('--strategy', '-s', default=None, help=f"Trading strategy.")

    p.add_argument('--list-exchanges', default=None, help=f"Show available exchanges.")
    p.add_argument('--list-strategies', default=None, help=f"Show available strategies.")


    app = Application(p.parse_args())
    app.run()

if __name__ == "__main__":
    main(sys.argv[1:])

