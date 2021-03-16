import operator
from enum import Enum, auto

import numpy as np
import pandas as pd
import talib
from chart import Chart
from customtypes import CurrencyPair, IStrategy, TradingMode
from termcolor import colored
from trade import Trade, TradeStatus
from util import (MIN_TREND_LINE_LENGTH, frame_trend, get_aprox_trend_line, is_downtrend, is_uptrend)


class TrendState(Enum):
    UNDEFINED = auto()
    UPTREND = auto()
    DOWNTREND = auto()


class Strategy(IStrategy):
    __strategy__ = 'default'

    def __init__(self, mode, budget, chart, exchange):
        self.exchange = exchange
        self.chart: Chart = chart
        self.pair: CurrencyPair = self.chart.pair
        self.mode: TradingMode = mode
        self.budget = budget

        self.trades = []
        self.currentPrice = 0
        self.current_candle = None
        self.max_num_trades = 1

        self.n_downtrend = MIN_TREND_LINE_LENGTH
        self.n_uptrend = MIN_TREND_LINE_LENGTH

        self.PREVIOUS_TREND = TrendState.UNDEFINED

    def preload(self, candle_list):
        self.chart.reset(candle_list)

    def on_tick(self, candle):
        self.chart.add(candle)
        self.current_candle = candle
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
        u, d = self.tick(candle, open_trades, df)

        self.update_open_trades()
        self.show_positions()

        return u, d

    def tick(self, candle, open_trades, df):
        curr_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        RSI = curr_row["RSI"]

        DI_P = curr_row["DI+"]
        DI_M = curr_row["DI-"]
        ADX = curr_row["ADX"]

        EMA50 = curr_row["EMA50"]
        EMA200 = curr_row["EMA200"]

        P_EMA50 = prev_row["EMA50"]
        P_EMA200 = prev_row["EMA200"]

        EMA_50_200_DEAD_CROSS = EMA200 > EMA50
        EMA_50_200_GOLDEN_CROSS = EMA50 > EMA200

        EMA200_FALLING = frame_trend(df, 5, "EMA200", operator.ge)
        EMA50_FALLING = frame_trend(df, 3, "EMA50", operator.ge)
        EMA50_RISING = frame_trend(df, 2, "EMA50", operator.le)

        RSI_RISING = frame_trend(df, 2, "RSI", operator.ge)

        price_lower_that_ema_200 = EMA200 > self.currentPrice
        price_upper_that_ema_200 = EMA200 < self.currentPrice
        price_lower_that_ema_50 = EMA50 > self.currentPrice
        price_upper_that_ema_50 = EMA50 < self.currentPrice

        prev_ema_50_200_diff = abs(P_EMA50 - P_EMA200)
        curr_ema_50_200_diff = abs(EMA50 - EMA200)

        can_open_new_trade = len(open_trades) < self.max_num_trades

        trade = Trade(self.pair, self.budget, self.mode, self.exchange, 5.0)

        indicator_y_uptrend = "High"
        indicator_y_downtrend = "Low"

        p_uptrend = get_aprox_trend_line(df, self.n_uptrend, indicator_y_downtrend)
        p_downtrend = get_aprox_trend_line(df, self.n_downtrend, indicator_y_uptrend)

        UP_TREND = is_uptrend(df, p_uptrend, indicator_y_uptrend)
        # UP_TREND = UP_TREND and operator.le(p_uptrend[0], p_uptrend[-1])
        # UP_TREND = UP_TREND and frame_trend(df, self.n_uptrend, indicator_y_uptrend, operator.le)

        DOWN_TREND = is_downtrend(df, p_downtrend, indicator_y_downtrend)
        # DOWN_TREND = DOWN_TREND and operator.ge(p_downtrend[0], p_downtrend[-1])
        # DOWN_TREND = DOWN_TREND and frame_trend(df, self.n_downtrend, indicator_y_downtrend, operator.ge)

        if UP_TREND == DOWN_TREND:
            self.n_uptrend = MIN_TREND_LINE_LENGTH
            self.n_downtrend = MIN_TREND_LINE_LENGTH
            return p_uptrend, p_downtrend

        # print(UP_TREND, DOWN_TREND)
        current_n_uptrend = [MIN_TREND_LINE_LENGTH, self.n_uptrend + 1][UP_TREND]
        current_n_downtrend = [MIN_TREND_LINE_LENGTH, self.n_downtrend + 1][DOWN_TREND]

        TREND_STATE = TrendState.UNDEFINED

        if UP_TREND and current_n_uptrend > self.n_uptrend:
            TREND_STATE = TrendState.UPTREND

        if DOWN_TREND and current_n_downtrend > self.n_downtrend:
            TREND_STATE = TrendState.DOWNTREND

        if can_open_new_trade:
            if TREND_STATE == TrendState.UPTREND:
                if self.PREVIOUS_TREND == TrendState.DOWNTREND:
                    if current_n_downtrend == MIN_TREND_LINE_LENGTH:
                        if RSI <= 60:
                            if trade.open(candle):
                                self.trades.append(trade)
        #--------------------------
        if TREND_STATE == TrendState.DOWNTREND:
            for trade in open_trades:
                if abs(trade.profit(candle)) >= 0.4:
                    trade.close(candle)
        #--------------------------

        self.n_uptrend = current_n_uptrend
        self.n_downtrend = current_n_downtrend
        self.PREVIOUS_TREND = TREND_STATE

        return p_uptrend, p_downtrend

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

        ema_3 = talib.EMA(np_prices_close, timeperiod=3)
        ema_50 = talib.EMA(np_prices_close, timeperiod=50)
        ema_200 = talib.EMA(np_prices_close, timeperiod=200)

        zipped = zip(timestamps, np_prices_open, np_prices_close, np_prices_high, np_prices_low, rsi, ema_3, ema_50,
                     ema_200, adx, di_minus, di_plus)
        columns = ["Timestamp", "Open", "Close", "High", "Low", "RSI", "EMA3", "EMA50", "EMA200", "ADX", "DI-", "DI+"]

        return pd.DataFrame(zipped, columns=columns)

    def update_open_trades(self):
        for trade in self.trades:
            if trade.status == TradeStatus.OPEN:
                trade.tick(self.current_candle)

    def show_positions(self):
        tradesProfitPercent = []
        for trade in self.trades:
            tradesProfitPercent.append(trade.showTrade())

        tradesProfitPercent = list(filter(bool, tradesProfitPercent))

        if tradesProfitPercent:
            profit = sum(tradesProfitPercent)
            pf = colored("{: 3.2f}%".format(profit), 'white', attrs=["bold"])

            print(f"Summary profit {pf}")
