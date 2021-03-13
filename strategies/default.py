from trade import Trade, TradeStatus
from chart import Chart
from customtypes import IStrategy
from util import frame_trend

from termcolor import colored
import talib
import numpy as np
import pandas as pd

import functools, operator

class Strategy(IStrategy):
    __strategy__ = 'default'

    def __init__(self, chart, exchange):
        self.exchange = exchange
        self.chart: Chart = chart

        self.trades = []
        self.currentPrice = 0
        self.max_num_trades = 1

    def preload(self, candle_list):
        self.chart.reset(candle_list)

    def on_tick(self, candle):
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

        # strategy tick
        self.tick(candle, open_trades, df)

        self.update_open_trades()
        self.show_positions()

    def tick(self, candle, open_trades, df):
        prev_row = df.iloc[-2]

        prev_ema_50 = prev_row["EMA50"]
        prev_ema_200 = prev_row["EMA200"]

        curr_row = df.iloc[-1]
        current_RSI = curr_row["RSI"]

        ema_50 = curr_row["EMA50"]
        ema_200 = curr_row["EMA200"]

        can_open_new_trade = len(open_trades) < self.max_num_trades

        ema_50_200_dead_cross = ema_200 > ema_50
        ema_50_200_golden_cross = ema_50 > ema_200

        ema_50_falling = ema_50 < prev_ema_50
        ema_50_rising = ema_50 > prev_ema_50

        prev_ema_50_200_diff = abs(prev_ema_50 - prev_ema_200)
        curr_ema_50_200_diff = abs(ema_50 - ema_200)

        ema_50_falling_x = frame_trend(df, 3, "EMA50", operator.gt)

        is_price_falling = frame_trend(df, 5, "Price.c", operator.gt)
        is_price_rising = frame_trend(df, 2, "Price.c", operator.lt)

        is_rsi_rising = frame_trend(df, 3, "RSI", operator.lt)

        price_lower_that_ema_200 = ema_200 > self.currentPrice
        price_lower_that_ema_50 = ema_50 > self.currentPrice
        price_upper_that_ema_50 = ema_50 < self.currentPrice

        rsi_overbought = current_RSI > 70
        rsi_overbought_crit = current_RSI >= 80
        rsi_oversold_light = current_RSI <= 40
        rsi_oversold = current_RSI < 30

        if can_open_new_trade:
            if price_lower_that_ema_50 or price_lower_that_ema_200:
                if is_price_falling:
                    trade = Trade(self.exchange, self.currentPrice, stopLossPercent=5.0, candle=candle)
                    self.trades.append(trade)

        if rsi_overbought_crit:
            for trade in open_trades:
                trade.close(self.currentPrice, candle=candle)

        elif ema_50_200_golden_cross:
            if ema_50_falling or is_rsi_rising: # with rsi is better
                for trade in open_trades:
                        trade.close(self.currentPrice, candle=candle)

        # ---------------------------------------------------------------------

        # if can_open_new_trade:
        #     if ema_50_200_dead_cross:
        #         # if prev_ema_50_200_diff > curr_ema_50_200_diff:
        #         # if ema_50_rising and price_lower_that_ema_50:
        #         if price_lower_that_ema_50 and not is_rsi_rising:
        #                 self.trades.append(Trade(self.exchange, self.currentPrice, stopLossPercent=5.0, candle=candle))

        #     # elif rsi_oversold and price_lower_that_ema_50:
        #     #     self.trades.append(Trade(self.exchange, self.currentPrice, stopLossPercent=5.0, candle=candle))

        # if ema_50_200_golden_cross:

        #     # if curr_ema_50_200_diff > prev_ema_50_200_diff: # with rsi is better
        #     if ema_50_falling or rsi_overbought: # with rsi is better
        #         for trade in open_trades:
        #                 trade.close(self.currentPrice, candle=candle)

        # elif rsi_overbought_crit:
        #     for trade in open_trades:
        #         trade.close(self.currentPrice, candle=candle)

    def get_indicators(self):
        candles = self.chart.get_candles()

        prices_close = list(map(lambda x: x.close, candles))
        np_prices_close = np.array(prices_close)

        prices_open = list(map(lambda x: x.open, candles))
        np_prices_open = np.array(prices_open)

        prices_high = list(map(lambda x: x.high, candles))
        np_prices_high = np.array(prices_high)

        prices_low = list(map(lambda x: x.low, candles))
        np_prices_low = np.array(prices_low)

        timestamps = list(map(lambda x: pd.to_datetime(x.timestamp, unit='s'), candles))

        rsi = talib.RSI(np_prices_close, timeperiod=14)
        adx = talib.ADX(np_prices_high, np_prices_low, np_prices_close, timeperiod=14)
        di_minus = talib.MINUS_DI(np_prices_high, np_prices_low, np_prices_close, timeperiod=14)
        di_plus = talib.PLUS_DI(np_prices_high, np_prices_low, np_prices_close, timeperiod=14)

        ema_50 = talib.EMA(np_prices_close, timeperiod=50)
        ema_200 = talib.EMA(np_prices_close, timeperiod=200)

        zipped = zip(timestamps, np_prices_close, np_prices_high, np_prices_low, rsi, ema_50, ema_200, adx, di_minus, di_plus)
        columns = ["Timestamp", "Price.c", "Price.h", "Price.l", "RSI", "EMA50", "EMA200", "ADX", "DI-", "DI+"]

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
