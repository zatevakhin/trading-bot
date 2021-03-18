import operator
from enum import Enum, auto

import numpy as np
import pandas as pd
import talib
from chart import Chart
from customtypes import CurrencyPair, TradingMode
from termcolor import colored
from trade import Trade, TradeStatus
from utils.trand_indicators import *

from strategies.strategybase import StrategyBase

MIN_TREND_LINE_LENGTH = 5


class TrendState(Enum):
    UNDEFINED = auto()
    UPTREND = auto()
    DOWNTREND = auto()


class Strategy(StrategyBase):
    __strategy__ = 'rvn.b'

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

        # DI_P = curr_row["DI+"]
        # DI_M = curr_row["DI-"]
        # ADX = curr_row["ADX"]

        EMA50 = curr_row["EMA50"]
        EMA200 = curr_row["EMA200"]

        # P_EMA50 = prev_row["EMA50"]
        # P_EMA200 = prev_row["EMA200"]

        EMA_50_200_DEAD_CROSS = EMA200 > EMA50
        EMA_50_200_GOLDEN_CROSS = EMA50 > EMA200

        # EMA200_FALLING = check_frame_trend(df, 5, "EMA200", operator.ge)
        # EMA50_FALLING = check_frame_trend(df, 3, "EMA50", operator.ge)
        # EMA50_RISING = check_frame_trend(df, 2, "EMA50", operator.le)

        # RSI_RISING = check_frame_trend(df, 2, "RSI", operator.ge)

        # price_lower_that_ema_200 = EMA200 > self.currentPrice
        # price_upper_that_ema_200 = EMA200 < self.currentPrice
        # price_lower_that_ema_50 = EMA50 > self.currentPrice
        # price_upper_that_ema_50 = EMA50 < self.currentPrice

        # prev_ema_50_200_diff = abs(P_EMA50 - P_EMA200)
        # curr_ema_50_200_diff = abs(EMA50 - EMA200)

        can_open_new_trade = len(open_trades) < self.max_num_trades

        trade = Trade(self.pair, self.budget, self.mode, self.exchange, 5.0)

        indicator_y_downtrend = "High"
        indicator_y_uptrend = "Low"

        p_uptrend = get_trend_aproximation(df, self.n_uptrend, indicator_y_uptrend)
        p_downtrend = get_trend_aproximation(df, self.n_downtrend, indicator_y_downtrend)

        ###
        ### TESTS
        ###
        # python app.py --pair RVN,USDT --exchange binance --mode backtest --t-start 1615932000 --t-end 1616065325 --period 1m --tick-b 0.1 --strategy rvn.b
        # Summary profit  9.95% / stupid
        # Summary profit  6.13% / not stupid

        # if EMA_50_200_GOLDEN_CROSS:
        #     UP_TREND = check_uptrend(df, p_uptrend, aggresive=True)
        #     DOWN_TREND = check_downtrend(df, p_downtrend, aggresive=True)
        # else:
        #     UP_TREND = check_uptrend(df, p_uptrend, aggresive=False)
        #     DOWN_TREND = check_downtrend(df, p_downtrend, aggresive=True)

        # Summary profit  4.99% / not stupid, aggr
        # Summary profit  0.59% / not stupid, not aggr

        # UP_TREND = check_uptrend(df, p_uptrend, aggresive=False)
        # DOWN_TREND = check_downtrend(df, p_downtrend, aggresive=False)

        # Summary profit  9.16% / stupid and aggr
        # Summary profit  10.02% / stupid and not aggr
        # Summary profit  10.02% / stupid and up trend aggr (EMA_50_200_GOLDEN_CROSS), down not aggr
        # Summary profit  10.02% / stupid and up and down trend aggr (EMA_50_200_GOLDEN_CROSS)
        # Summary profit  10.02% / stupid and down trend aggr (EMA_50_200_GOLDEN_CROSS), up not aggr

        # UP_TREND = stupid_check_uptrend(df, p_uptrend, aggresive=False)
        # DOWN_TREND = stupid_check_downtrend(df, p_downtrend, aggresive=False)

        # Trades done: 34, Summary profit:  9.90%
        # MIN_TREND_LINE_LENGTH = 2
        # Trades done: 34, Summary profit:  10.02%
        # MIN_TREND_LINE_LENGTH = 3
        # Trades done: 34, Summary profit:  10.02%
        # MIN_TREND_LINE_LENGTH = 4
        # Trades done: 32, Summary profit:  10.94%
        # MIN_TREND_LINE_LENGTH = 5
        # Trades done: 33, Summary profit:  10.77%
        # MIN_TREND_LINE_LENGTH = 6

        ###
        ### TESTS END
        ###

        UP_TREND = stupid_check_uptrend(df, p_uptrend, aggresive=False)
        DOWN_TREND = stupid_check_downtrend(df, p_downtrend, aggresive=False)

        TREND_STATE = TrendState.UNDEFINED

        if UP_TREND == DOWN_TREND:
            self.n_uptrend = MIN_TREND_LINE_LENGTH
            self.n_downtrend = MIN_TREND_LINE_LENGTH

        current_n_uptrend = [MIN_TREND_LINE_LENGTH, self.n_uptrend + 1][UP_TREND]
        current_n_downtrend = [MIN_TREND_LINE_LENGTH, self.n_downtrend + 1][DOWN_TREND]

        if UP_TREND:
            TREND_STATE = TrendState.UPTREND

        if DOWN_TREND:
            TREND_STATE = TrendState.DOWNTREND

        print(self.PREVIOUS_TREND, TREND_STATE)

        if can_open_new_trade:
            if TREND_STATE in [TrendState.UPTREND, TrendState.UNDEFINED]:
                if self.PREVIOUS_TREND in [TrendState.DOWNTREND]:
                    if RSI <= 50:
                        if trade.open(candle):
                            self.trades.append(trade)

        #--------------------------

        if TREND_STATE in [TrendState.DOWNTREND, TrendState.UNDEFINED]:
            if self.PREVIOUS_TREND in [TrendState.UPTREND]:
                for trade in open_trades:
                    if abs(trade.profit(candle)) >= 0.5:
                        trade.close(candle)

        #--------------------------
        if TREND_STATE == TrendState.UNDEFINED:
            for trade in open_trades:
                trade.set_prop_limit(candle, 0.6)

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
            tf = colored("{}".format(len(tradesProfitPercent)), 'yellow')

            print(f"Trades done: {tf}, Summary profit: {pf}")
