import indicators
from trade import Trade, TradeStatus
from chart import Chart

from enum import Enum, auto
from termcolor import colored
import talib
import numpy as np
import pandas as pd


class Strategy(object):
    def __init__(self, chart, exchange):
        self.exchange = exchange
        self.chart: Chart = chart

        self.trades = []
        self.currentPrice = 0
        self.max_num_trades = 1
        self.df = []

    def set_dataframe(self, df):
        self.df = df

    def preload(self, candle_list):
        self.chart.reset(candle_list)

        df = self.get_indicators()


    def tick(self, candle):
        self.chart.add(candle)
        self.currentPrice = float(candle.average)

        df = self.get_indicators()

        open_trades = []
        for trade in self.trades:
            if trade.status == TradeStatus.OPEN:
                open_trades.append(trade)

        price_fmt = colored("{:0.8f}".format(candle.average), 'cyan')
        pair_fmt = colored("{}".format(self.chart.pair), 'yellow')
        open_trades_fmt = colored("{}".format(len(open_trades)), 'magenta')


        print(f"Pair: {pair_fmt} Price: {price_fmt} Open trades {open_trades_fmt}")


        def is_falling(n, indicator):
            p_x = 0
            x_a = []
            for x in list(df.iloc[-n:][indicator]):
                x_a.append(p_x >= x)
                p_x = x

            return x_a.count(False) > x_a.count(True)


        prev_row = df.iloc[-2]
        prev_MACD = prev_row["MACD"]
        prev_MACDs = prev_row["MACDs"]

        prev_ema_50 = prev_row["EMA50"]
        prev_ema_200 = prev_row["EMA200"]

        curr_row = df.iloc[-1]
        current_RSI = curr_row["RSI"]
        current_MACD = curr_row["MACD"]
        current_MACDs = curr_row["MACDs"]
        ema_50 = curr_row["EMA50"]
        ema_200 = curr_row["EMA200"]

        can_open_new_trade = len(open_trades) < self.max_num_trades

        ema_50_200_dead_cross = ema_200 > ema_50
        ema_50_200_golden_cross = ema_50 > ema_200

        ema_50_falling = ema_50 < prev_ema_50
        ema_50_rising = ema_50 > prev_ema_50

        prev_ema_50_200_diff = abs(prev_ema_50 - prev_ema_200)
        curr_ema_50_200_diff = abs(ema_50 - ema_200)

        ema_50_falling_x = is_falling(3, "EMA50")
        ema_50_rising_x = not is_falling(3, "EMA50")

        price_lower_that_ema_50 = ema_50 > self.currentPrice
        price_upper_that_ema_50 = ema_50 < self.currentPrice

        rsi_overbought = current_RSI > 70
        rsi_overbought_crit = current_RSI >= 80
        rsi_oversold = current_RSI < 30


        if can_open_new_trade:
            if ema_50_200_dead_cross:
                # if prev_ema_50_200_diff > curr_ema_50_200_diff:
                # if ema_50_rising and price_lower_that_ema_50:
                if price_lower_that_ema_50 and not is_falling(3, "RSI"):
                        self.trades.append(Trade(self.exchange, self.currentPrice, stopLossPercent=5.0, candle=candle))

            # elif rsi_oversold and price_lower_that_ema_50:
            #     self.trades.append(Trade(self.exchange, self.currentPrice, stopLossPercent=5.0, candle=candle))

        if ema_50_200_golden_cross:

            # if curr_ema_50_200_diff > prev_ema_50_200_diff: # with rsi is better
            if ema_50_falling or rsi_overbought: # with rsi is better
                for trade in open_trades:
                        trade.close(self.currentPrice, candle=candle)

        elif rsi_overbought_crit:
            for trade in open_trades:
                trade.close(self.currentPrice, candle=candle)


        self.update_open_trades()
        self.show_positions()


    def get_indicators(self):
        candles = self.chart.get_candles()

        prices = list(map(lambda x: x.close, candles))
        np_prices = np.array(prices)

        timestamps = list(map(lambda x: pd.to_datetime(x.timestamp, unit='s'), candles))

        macd, macd_s, _ = talib.MACD(np_prices, fastperiod=12, slowperiod=26, signalperiod=9)

        rsi = talib.RSI(np_prices, timeperiod=14)

        ema_50 = talib.EMA(np_prices, timeperiod=50)
        ema_200 = talib.EMA(np_prices, timeperiod=200)

        zipped = zip(timestamps, np_prices, macd, macd_s, rsi, ema_50, ema_200)
        columns = ["Timestamp", "Price", "MACD", "MACDs", "RSI", "EMA50", "EMA200"]

        return pd.DataFrame(zipped, columns=columns)


    def update_open_trades(self):
        for trade in self.trades:
            if trade.status == TradeStatus.OPEN:
                trade.tick(self.currentPrice)

    def show_positions(self):
        tradesProfitPercent = []
        for trade in self.trades:
            tradesProfitPercent.append(trade.showTrade())

        tradesProfitPercent = list(filter(bool, tradesProfitPercent))

        if tradesProfitPercent:
            profit = sum(tradesProfitPercent)
            pf = colored("{: 3.2f}%".format(profit), 'white', attrs=["bold"])

            print(f"Summary profit {pf}")
